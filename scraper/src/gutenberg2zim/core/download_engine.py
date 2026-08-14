"""Generic HTTP download engine.

Source-agnostic downloader with a persistent session, retry with backoff, and
optional on-disk caching keyed by URL hash. Sources hand it `DownloadRequest`s
(from their `FormatResolverPort`); it knows nothing about any specific
source's URL scheme.
"""

import hashlib
import io
import threading
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import backoff
import requests
from requests.adapters import HTTPAdapter

from gutenberg2zim.constants import DEFAULT_HTTP_TIMEOUT, DL_CHUNCK_SIZE, logger
from gutenberg2zim.core.ports import DownloadRequest


@dataclass(frozen=True, slots=True)
class DownloadResult:
    url: str
    path: Path
    size: int
    from_cache: bool


def is_fatal_http_error(exc: Exception) -> bool:
    """Give up on error codes 400-499 except 429"""
    return (
        isinstance(exc, requests.HTTPError)
        and exc.response is not None
        and HTTPStatus.BAD_REQUEST
        <= exc.response.status_code
        < HTTPStatus.INTERNAL_SERVER_ERROR
        and exc.response.status_code != HTTPStatus.TOO_MANY_REQUESTS
    )


def fetch_bytes_with_retry(
    url: str,
    session: requests.Session | None = None,
    timeout: int = DEFAULT_HTTP_TIMEOUT,
    max_retry_time: int = 30,
) -> bytes:
    """GET `url` and return its full content, retrying transient errors.

    Retry lives at the individual-download level: transient network errors
    are retried with exponential backoff, while fatal HTTP errors (4xx
    except 429) give up immediately by raising.
    """
    get = session.get if session is not None else requests.get

    # logger=None: backoff's own "giving up" messages would fire at ERROR
    # level for routine 404s (books that simply lack a format on the
    # mirror); the caller logs failures with proper context instead
    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_time=max_retry_time,
        giveup=is_fatal_http_error,
        logger=None,
    )
    def _attempt() -> bytes:
        with get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            content = io.BytesIO()
            for chunk in response.iter_content(chunk_size=DL_CHUNCK_SIZE):
                if chunk:
                    content.write(chunk)
            return content.getvalue()

    return _attempt()


class DownloadEngine:
    def __init__(
        self,
        cache_dir: Path | None = None,
        session: requests.Session | None = None,
        timeout: int = DEFAULT_HTTP_TIMEOUT,
        max_retry_time: int = 30,
    ):
        self._cache_dir = cache_dir.resolve() if cache_dir else None
        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        # Explicit session (mainly tests) or per-worker-thread sessions:
        # requests.Session is not guaranteed thread-safe, so each worker
        # thread gets its own lazily-created persistent session
        self._injected_session = session
        self._local = threading.local()
        # Track every lazily-created thread-local session so close() can
        # release their connection pools at the end of the run
        self._sessions: list[requests.Session] = []
        self._sessions_lock = threading.Lock()
        self._timeout = timeout
        self._max_retry_time = max_retry_time

    def _get_session(self) -> requests.Session:
        if self._injected_session is not None:
            return self._injected_session
        session = getattr(self._local, "session", None)
        if session is None:
            session = requests.Session()
            session.mount("https://", HTTPAdapter(max_retries=3))
            session.mount("http://", HTTPAdapter(max_retries=3))
            self._local.session = session
            with self._sessions_lock:
                self._sessions.append(session)
        return session

    def close(self) -> None:
        """Close the injected session and all per-thread sessions"""
        if self._injected_session is not None:
            self._injected_session.close()
        with self._sessions_lock:
            sessions, self._sessions = self._sessions, []
        for session in sessions:
            session.close()

    def cache_path_for(self, url: str) -> Path:
        """Deterministic cache path for a URL (hash + original suffix)"""
        if self._cache_dir is None:
            raise RuntimeError("A cache directory is required for cached downloads")
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        suffix = Path(urlparse(url).path).suffix
        return self._cache_dir / f"{digest}{suffix}"

    @property
    def cache_enabled(self) -> bool:
        """Whether downloads without an explicit target can be cached."""
        return self._cache_dir is not None

    def fetch_bytes(self, url: str) -> bytes:
        """GET `url` and return its full content, retrying transient errors.

        Uses this engine's per-thread session, timeout and retry budget.
        """
        return fetch_bytes_with_retry(
            url,
            session=self._get_session(),
            timeout=self._timeout,
            max_retry_time=self._max_retry_time,
        )

    def content_type(self, url: str) -> str | None:
        """Return a URL's final content type without downloading its body.

        A missing or unsupported HEAD response is deliberately inconclusive:
        callers can fall back to a normal download and inspect the content.
        """
        try:
            with self._get_session().head(
                url, allow_redirects=True, timeout=self._timeout
            ) as response:
                response.raise_for_status()
                return response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        except requests.RequestException:
            return None

    def download(
        self, request: DownloadRequest, dest: Path | None = None
    ) -> DownloadResult:
        """Download `request.url` to `dest` (or request.target, or the cache).

        Returns the cached file directly when the URL was downloaded before
        and no explicit destination is requested.
        """
        target = dest or request.target
        if target is None and self._cache_dir is None:
            raise RuntimeError(
                "A download target is required when no cache directory is configured"
            )

        cache_path = self.cache_path_for(request.url) if self._cache_dir else None

        if target is None and cache_path is not None and cache_path.exists():
            logger.debug(f"\t\tCache hit for {request.url}")
            return DownloadResult(
                url=request.url,
                path=cache_path,
                size=cache_path.stat().st_size,
                from_cache=True,
            )

        target = target or cache_path
        if target is None:
            raise RuntimeError("Unable to determine a download target")
        self._download_with_retry(request.url, target)
        return DownloadResult(
            url=request.url,
            path=target,
            size=target.stat().st_size,
            from_cache=False,
        )

    def _download_with_retry(self, url: str, target: Path) -> None:
        @backoff.on_exception(
            backoff.expo,
            requests.exceptions.RequestException,
            max_time=self._max_retry_time,
            giveup=is_fatal_http_error,
            logger=logger,
        )
        def _attempt():
            with self._get_session().get(
                url, stream=True, timeout=self._timeout
            ) as response:
                response.raise_for_status()
                target.parent.mkdir(parents=True, exist_ok=True)
                # Unique tmp name: concurrent downloads of the same URL must not collide
                unique_suffix = f"{target.suffix}.{uuid.uuid4().hex}.part"
                tmp_path = target.with_suffix(unique_suffix)
                with open(tmp_path, "wb") as fh:
                    for chunk in response.iter_content(chunk_size=DL_CHUNCK_SIZE):
                        if chunk:
                            fh.write(chunk)
                tmp_path.replace(target)

        _attempt()
