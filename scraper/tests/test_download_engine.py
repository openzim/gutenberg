"""Tests for core.download_engine."""

import threading
from unittest.mock import MagicMock

import pytest
import requests
from requests.adapters import HTTPAdapter

from gutenberg2zim.core.download_engine import DownloadEngine, fetch_bytes_with_retry
from gutenberg2zim.core.ports import DownloadRequest

URL = "https://example.org/books/12345.epub"


def _streaming_response(chunks: list[bytes]) -> MagicMock:
    """Mock response behaving like a `stream=True` requests response"""
    resp = MagicMock(name="response")
    resp.__enter__.return_value = resp
    resp.raise_for_status.return_value = None
    resp.iter_content.return_value = iter(chunks)
    return resp


def _http_error(status_code: int) -> requests.HTTPError:
    error = requests.HTTPError(f"{status_code} error")
    error.response = MagicMock(status_code=status_code)
    return error


@pytest.fixture
def session():
    return MagicMock(name="session")


@pytest.fixture
def engine(tmp_path, session):
    return DownloadEngine(cache_dir=tmp_path / "cache", session=session)


def test_streams_chunks_to_disk(engine, session):
    session.get.return_value = _streaming_response([b"epub-", b"data-", b"chunks"])

    result = engine.download(DownloadRequest(url=URL, format_name="epub"))

    assert result.path == engine.cache_path_for(URL)
    assert result.path.read_bytes() == b"epub-data-chunks"
    assert result.size == len(b"epub-data-chunks")
    assert not result.from_cache
    # streamed, not fetched whole
    session.get.assert_called_once_with(URL, stream=True, timeout=engine._timeout)
    # no temporary .part file left behind (atomic rename happened)
    assert not list(result.path.parent.glob("*.part"))


def test_cache_hit_skips_http(engine, session):
    session.get.return_value = _streaming_response([b"cached"])

    first = engine.download(DownloadRequest(url=URL, format_name="epub"))
    session.get.reset_mock()
    second = engine.download(DownloadRequest(url=URL, format_name="epub"))

    assert second.from_cache
    assert second.path == first.path
    assert second.size == first.size
    session.get.assert_not_called()


def test_explicit_target_is_honored(engine, session, tmp_path):
    session.get.return_value = _streaming_response([b"payload"])
    dest = tmp_path / "out" / "book.epub"

    result = engine.download(DownloadRequest(url=URL, format_name="epub"), dest=dest)

    assert result.path == dest
    assert dest.read_bytes() == b"payload"
    # parent directory was created
    assert dest.parent.exists()


def test_explicit_target_does_not_require_or_create_a_cache(tmp_path, session):
    engine = DownloadEngine(session=session)
    session.get.return_value = _streaming_response([b"payload"])
    dest = tmp_path / "out" / "book.epub"

    result = engine.download(DownloadRequest(url=URL, format_name="epub"), dest=dest)

    assert result.path == dest
    assert result.path.read_bytes() == b"payload"
    assert not engine.cache_enabled


def test_retries_transient_error_then_succeeds(engine, session):
    session.get.side_effect = [
        requests.ConnectionError("connection reset"),
        _streaming_response([b"after-retry"]),
    ]

    result = engine.download(DownloadRequest(url=URL, format_name="epub"))

    assert result.path.read_bytes() == b"after-retry"
    assert session.get.call_count == 2


def test_fatal_4xx_gives_up_without_retry(engine, session):
    resp = _streaming_response([])
    resp.raise_for_status.side_effect = _http_error(404)
    session.get.return_value = resp

    with pytest.raises(requests.HTTPError):
        engine.download(DownloadRequest(url=URL, format_name="epub"))

    session.get.assert_called_once()


def test_cache_path_is_deterministic_and_keeps_suffix(engine):
    assert engine.cache_path_for(URL) == engine.cache_path_for(URL)
    assert engine.cache_path_for(URL).suffix == ".epub"


# persistent per-worker-thread sessions
def test_same_thread_reuses_persistent_session(tmp_path):
    engine = DownloadEngine(cache_dir=tmp_path / "cache")
    assert engine._get_session() is engine._get_session()


def test_each_thread_gets_its_own_session(tmp_path):
    engine = DownloadEngine(cache_dir=tmp_path / "cache")
    sessions = {}
    barrier = threading.Barrier(2)

    def grab(key):
        barrier.wait()  # force both threads to be alive concurrently
        sessions[key] = engine._get_session()

    threads = [threading.Thread(target=grab, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sessions[0] is not sessions[1]


def test_worker_session_has_mounted_retries(tmp_path):
    engine = DownloadEngine(cache_dir=tmp_path / "cache")
    session = engine._get_session()
    for scheme in ("https://", "http://"):
        adapter = session.get_adapter(f"{scheme}example.org")
        assert isinstance(adapter, HTTPAdapter)
        assert adapter.max_retries.total == 3


def test_injected_session_takes_precedence(tmp_path, session):
    engine = DownloadEngine(cache_dir=tmp_path / "cache", session=session)
    assert engine._get_session() is session


# granular per-download retry
def test_fetch_bytes_retries_transient_error(session):
    session.get.side_effect = [
        requests.ConnectionError("connection reset"),
        _streaming_response([b"retried", b"-ok"]),
    ]

    content = fetch_bytes_with_retry(URL, session=session)

    assert content == b"retried-ok"
    assert session.get.call_count == 2


def test_fetch_bytes_gives_up_immediately_on_fatal_4xx(session):
    resp = _streaming_response([])
    resp.raise_for_status.side_effect = _http_error(404)
    session.get.return_value = resp

    with pytest.raises(requests.HTTPError):
        fetch_bytes_with_retry(URL, session=session)

    session.get.assert_called_once()
