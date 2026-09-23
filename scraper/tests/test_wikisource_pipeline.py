"""Tests for Wikisource per-work processing."""

from io import BytesIO
from unittest.mock import MagicMock, patch
from zipfile import ZIP_STORED, ZipFile

from gutenberg2zim.core.models import Format, Work
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.core.progress import ScraperProgress
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.sources.wikisource.pipeline import WikisourcePipeline


def _work() -> Work:
    return Work(
        id="en_first-book-12345678",
        source="wikisource",
        title="First Book",
        formats=[
            Format(
                name="epub",
                media_type="application/epub+zip",
                url="https://ws-export.wmcloud.org/?lang=en&format=epub&page=First_Book",
            )
        ],
    )


def _pipeline(work: Work, engine: MagicMock, assembler: MagicMock):
    metadata = MagicMock()
    metadata.fetch.return_value = [work]
    return WikisourcePipeline(
        metadata=metadata,
        store=WorkStore(),
        assembler=assembler,
        progress=ScraperProgress(None),
        concurrency=1,
        formats=["epub", "pdf", "html"],
        zim_name="test",
        source_slug="wikisource",
        display_name="Wikisource",
        title_search=False,
        engine=engine,
    )


def _valid_epub() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_STORED) as archive:
        archive.writestr("mimetype", "application/epub+zip")
    return output.getvalue()


def test_process_ref_downloads_epub_and_marks_the_rest_unsupported():
    work = _work()
    engine = MagicMock()
    engine.fetch_bytes.return_value = _valid_epub()
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)

    with patch(
        "gutenberg2zim.sources.wikisource.pipeline.extract_cover",
        return_value=None,
    ):
        pipeline.process_ref(WorkRef(id=work.id, source="wikisource"))

    assert pipeline.store.get("wikisource", work.id) is work
    assert work.extra["unsupported_formats"] == ["pdf", "html"]
    assembler.add_item_for.assert_called_once_with(
        path=f"First Book.{work.id}.epub",
        content=_valid_epub(),
        mimetype="application/epub+zip",
        is_front=False,
    )


def test_process_ref_rejects_an_html_response_at_the_epub_url():
    work = _work()
    engine = MagicMock()
    engine.fetch_bytes.return_value = b"<!DOCTYPE html><html><body>nope</body></html>"
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)

    pipeline.process_ref(WorkRef(id=work.id, source="wikisource"))

    assert pipeline.store.get("wikisource", work.id) is None
    assembler.add_item_for.assert_not_called()


def test_process_ref_attaches_a_cover_when_extractable():
    work = _work()
    engine = MagicMock()
    engine.fetch_bytes.return_value = _valid_epub()
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)

    with patch(
        "gutenberg2zim.sources.wikisource.pipeline.extract_cover",
        return_value=b"cover bytes",
    ):
        pipeline.process_ref(WorkRef(id=work.id, source="wikisource"))

    assert work.extra["has_cover"] is True
    assert work.cover is not None
    assembler.add_item_for.assert_any_call(
        path=f"covers/{work.id}_cover_image.webp",
        content=b"cover bytes",
        mimetype="image/webp",
        is_front=False,
    )
