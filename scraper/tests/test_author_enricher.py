"""Tests for gutenberg author enrichment (bio + portrait from Wikipedia)."""

import io
from unittest.mock import MagicMock

import requests
from PIL import Image

from gutenberg2zim.core.models import Creator, Work
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.sources.gutenberg.author_enricher import (
    enrich_authors,
    enrich_creator,
    fetch_author_summary,
    wikipedia_title,
)

SUMMARY_JSON = b'{"extract": "A short biography.", "thumbnail": {"source": "https://upload.wikimedia.org/thumb.jpg"}}'


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(buffer, format="JPEG")
    return buffer.getvalue()


def _arrow_creator() -> Creator:
    return Creator(
        id="68",
        name="Jane Austen",
        extra={
            "first_names": "Jane",
            "webpage_resource": "https://en.wikipedia.org/wiki/Jane_Austen",
        },
    )


def _store_with_creator(creator: Creator) -> WorkStore:
    store = WorkStore()
    store.add(Work(id="1", source="gutenberg", title="Emma", creators=[creator]))
    return store


def test_wikipedia_title_extracts_english_wikipedia_pages():
    assert wikipedia_title(_arrow_creator()) == "Jane_Austen"
    assert wikipedia_title(Creator(id="1", name="No Link")) is None
    assert (
        wikipedia_title(
            Creator(
                id="2",
                name="Personal Site",
                extra={"webpage_resource": "https://example.org/about"},
            )
        )
        is None
    )


def test_fetch_author_summary_returns_json():
    engine = MagicMock(name="engine")
    engine.fetch_bytes.return_value = SUMMARY_JSON

    summary = fetch_author_summary(engine, "Jane_Austen")
    assert summary is not None
    assert summary["extract"] == "A short biography."
    engine.fetch_bytes.assert_called_once_with(
        "https://en.wikipedia.org/api/rest_v1/page/summary/Jane_Austen"
    )


def test_fetch_author_summary_handles_missing_page_and_bad_payload():
    engine = MagicMock(name="engine")
    engine.fetch_bytes.return_value = (
        b'{"type": "https://mediawiki.org/wiki/HyperSwitch/errors/not_found"}'
    )
    assert fetch_author_summary(engine, "No_Such_Author") is None

    engine.fetch_bytes.return_value = b"not json"
    assert fetch_author_summary(engine, "Bad") is None

    def raise_connection_error(*_args, **_kwargs):
        raise requests.ConnectionError("offline")

    engine.fetch_bytes.side_effect = raise_connection_error
    assert fetch_author_summary(engine, "Offline") is None


def test_enrich_creator_sets_bio_portrait_and_skips_without_link():
    engine = MagicMock(name="engine")
    engine.fetch_bytes.side_effect = [SUMMARY_JSON, _jpeg_bytes()]
    assembler = MagicMock(name="assembler")

    enriched = enrich_creator(_arrow_creator(), engine, assembler)

    assert enriched.extra["bio"] == "A short biography."
    assert enriched.extra["portrait_path"] == "authors/68.webp"
    assembler.add_item_for.assert_called_once()
    call = assembler.add_item_for.call_args
    assert call.kwargs["path"] == "authors/68.webp"
    assert call.kwargs["mimetype"] == "image/webp"
    assert isinstance(call.kwargs["content"], bytes) and call.kwargs["content"]

    engine.fetch_bytes.reset_mock()
    unchanged = enrich_creator(Creator(id="216", name="Anonymous"), engine, assembler)
    assert unchanged == Creator(id="216", name="Anonymous")
    engine.fetch_bytes.assert_not_called()


def test_enrich_creator_without_portrait_keeps_bio_only():
    engine = MagicMock(name="engine")
    engine.fetch_bytes.return_value = b'{"extract": "Only a bio here."}'
    assembler = MagicMock(name="assembler")

    enriched = enrich_creator(_arrow_creator(), engine, assembler)

    assert enriched.extra["bio"] == "Only a bio here."
    assert "portrait_path" not in enriched.extra
    assembler.add_item_for.assert_not_called()


def test_enrich_creator_recovers_from_portrait_errors():
    engine = MagicMock(name="engine")

    def side_effect(url, **_kwargs):
        if url.startswith("https://en.wikipedia.org/api/rest_v1"):
            return SUMMARY_JSON
        raise requests.ConnectionError("image down")

    engine.fetch_bytes.side_effect = side_effect
    assembler = MagicMock(name="assembler")

    enriched = enrich_creator(_arrow_creator(), engine, assembler)

    assert enriched.extra["bio"] == "A short biography."
    assert "portrait_path" not in enriched.extra
    assembler.add_item_for.assert_not_called()


def test_enrich_authors_updates_store_and_deduplicates():
    engine = MagicMock(name="engine")
    engine.fetch_bytes.side_effect = [SUMMARY_JSON, _jpeg_bytes()]
    assembler = MagicMock(name="assembler")

    store = _store_with_creator(_arrow_creator())
    store.add(
        Work(
            id="2",
            source="gutenberg",
            title="Pride and Prejudice",
            creators=[_arrow_creator()],
        )
    )

    enrich_authors(store, engine, assembler, concurrency=2)

    creators = {work.creators[0].id: work.creators[0] for work in store.works}
    assert creators["68"].extra["bio"] == "A short biography."
    assert creators["68"].extra["portrait_path"] == "authors/68.webp"
    assert engine.fetch_bytes.call_count == 2


def test_enrich_authors_ignores_authors_without_wikipedia():
    engine = MagicMock(name="engine")
    assembler = MagicMock(name="assembler")
    store = _store_with_creator(Creator(id="216", name="Anonymous"))

    enrich_authors(store, engine, assembler, concurrency=1)

    assert store.works[0].creators[0].extra == {}
    engine.fetch_bytes.assert_not_called()
    assembler.add_item_for.assert_not_called()


def test_enrich_authors_keeps_running_when_some_authors_fail():
    engine = MagicMock(name="engine")
    engine.fetch_bytes.side_effect = requests.ConnectionError("offline")
    assembler = MagicMock(name="assembler")
    store = _store_with_creator(_arrow_creator())

    enrich_authors(store, engine, assembler, concurrency=1)

    assert store.works[0].creators[0].extra.get("webpage_resource")
    assert "bio" not in store.works[0].creators[0].extra


def test_enrich_authors_handles_empty_store():
    engine = MagicMock(name="engine")
    assembler = MagicMock(name="assembler")

    enrich_authors(WorkStore(), engine, assembler, concurrency=1)

    engine.fetch_bytes.assert_not_called()
    assembler.add_item_for.assert_not_called()
