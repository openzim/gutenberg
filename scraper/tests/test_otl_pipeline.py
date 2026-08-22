"""Tests for OTL per-work processing."""

from unittest.mock import MagicMock, patch

from gutenberg2zim.core.models import Format, Work
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.core.progress import ScraperProgress
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.sources.opentextbooks.pipeline import OpenTextbookLibraryPipeline


def _pipeline(work: Work, engine: MagicMock, assembler: MagicMock):
    metadata = MagicMock()
    metadata.fetch.return_value = [work]
    return OpenTextbookLibraryPipeline(
        metadata=metadata,
        store=WorkStore(),
        assembler=assembler,
        progress=ScraperProgress(None),
        concurrency=1,
        formats=["epub", "pdf", "html"],
        zim_name="test",
        source_slug="opentextbooks",
        display_name="Open Textbook Library",
        title_search=False,
        engine=engine,
    )


def test_process_ref_exports_direct_files_and_marks_unavailable_formats():
    work = Work(
        id="10",
        source="opentextbooks",
        title="Calculus",
        formats=[
            Format(
                name="PDF",
                media_type="application/pdf",
                url="https://example.org/calculus.pdf",
            )
        ],
    )
    engine = MagicMock()
    engine.content_type.return_value = "application/pdf"
    engine.fetch_bytes.return_value = b"%PDF-1.7 pdf bytes"
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)

    pipeline.process_ref(WorkRef(id="10", source="opentextbooks"))

    assert pipeline.store.get("opentextbooks", "10") is work
    assert work.extra["unsupported_formats"] == ["epub", "html"]
    assembler.add_item_for.assert_called_once_with(
        path="Calculus.10.pdf",
        content=b"%PDF-1.7 pdf bytes",
        mimetype="application/pdf",
        is_front=False,
    )


def test_run_exports_a_downloaded_otl_work_without_popularity_metrics():
    work = Work(
        id="10",
        source="opentextbooks",
        title="Calculus",
        formats=[
            Format(
                name="PDF",
                media_type="application/pdf",
                url="https://example.org/calculus.pdf",
            )
        ],
    )
    engine = MagicMock()
    engine.content_type.return_value = "application/pdf"
    engine.fetch_bytes.return_value = b"%PDF-1.7 pdf bytes"
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)

    with (
        patch(
            "gutenberg2zim.sources.opentextbooks.pipeline.extract_cover",
            return_value=b"cover bytes",
        ),
        patch("gutenberg2zim.core.pipeline.export_search_items") as search_items,
        patch("gutenberg2zim.core.pipeline.generate_json_files") as json_files,
        patch("gutenberg2zim.core.pipeline.generate_noscript_pages") as nojs_pages,
    ):
        pipeline.run([WorkRef(id="10", source="opentextbooks")])

    assert work.popularity is None
    assert work.extra["has_cover"] is True
    assert work.cover is not None
    assembler.add_item_for.assert_any_call(
        path="covers/10_cover_image.webp",
        content=b"cover bytes",
        mimetype="image/webp",
        is_front=False,
    )
    search_items.assert_called_once()
    json_files.assert_called_once()
    nojs_pages.assert_called_once()


def test_process_ref_rejects_an_html_landing_page_at_a_pdf_url():
    work = Work(
        id="10",
        source="opentextbooks",
        title="Calculus",
        formats=[
            Format(
                name="PDF",
                media_type="application/pdf",
                url="https://example.org/calculus.pdf",
            )
        ],
    )
    engine = MagicMock()
    html = b"<!doctype html><html><body>Textbook</body></html>"
    engine.fetch_bytes.return_value = html
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)

    with patch(
        "gutenberg2zim.sources.opentextbooks.pipeline.fetch_page_cover"
    ) as fetch_cover:
        pipeline.process_ref(WorkRef(id="10", source="opentextbooks"))

    assert pipeline.store.get("opentextbooks", "10") is None
    assert work.extra["unsupported_formats"] == ["epub", "pdf", "html"]
    assembler.add_item_for.assert_not_called()
    fetch_cover.assert_not_called()


def test_html_controls_only_receive_validated_binary_formats():
    work = Work(
        id="10",
        source="opentextbooks",
        title="Calculus",
        formats=[
            Format(
                name="PDF",
                media_type="application/pdf",
                url="https://example.org/calculus.pdf",
            ),
            Format(
                name="Online",
                media_type="text/html",
                url="https://example.org/calculus/",
            ),
        ],
    )
    engine = MagicMock()
    engine.fetch_bytes.return_value = b"<!doctype html><html></html>"
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)
    edition = MagicMock(pages={"Calculus.10": b"<!doctype html><html></html>"})

    with patch(
        "gutenberg2zim.sources.opentextbooks.pipeline.download_html_edition",
        return_value=edition,
    ) as mirror:
        pipeline.process_ref(WorkRef(id="10", source="opentextbooks"))

    assert mirror.call_args.args == (
        engine,
        work,
        "https://example.org/calculus/",
        ["html"],
    )
    assert work.extra["unsupported_formats"] == ["epub", "pdf"]
    assert b"html-reader-btn-pdf" not in edition.pages["Calculus.10"]


def test_html_is_not_mirrored_when_a_binary_format_is_available_after_it():
    work = Work(
        id="10",
        source="opentextbooks",
        title="Calculus",
        formats=[
            Format(
                name="PDF",
                media_type="application/pdf",
                url="https://example.org/calculus.pdf",
            ),
            Format(
                name="Online",
                media_type="text/html",
                url="https://example.org/calculus/",
            ),
        ],
    )
    engine = MagicMock()
    engine.fetch_bytes.return_value = b"%PDF-1.7 pdf bytes"
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)
    pipeline.formats = ["html", "pdf"]
    edition = MagicMock(pages={"Calculus.10": b"<!doctype html><html></html>"})

    with (
        patch(
            "gutenberg2zim.sources.opentextbooks.pipeline.download_html_edition",
            return_value=edition,
        ) as mirror,
    ):
        pipeline.process_ref(WorkRef(id="10", source="opentextbooks"))

    mirror.assert_not_called()
    assert work.extra["unsupported_formats"] == ["html"]
    assembler.add_item_for.assert_called_once_with(
        path="Calculus.10.pdf",
        content=b"%PDF-1.7 pdf bytes",
        mimetype="application/pdf",
        is_front=False,
    )


def test_process_ref_accepts_a_valid_epub_archive():
    work = Work(
        id="10",
        source="opentextbooks",
        title="Calculus",
        formats=[
            Format(
                name="eBook",
                media_type="application/epub+zip",
                url="https://example.org/calculus.epub",
            )
        ],
    )
    engine = MagicMock()
    engine.fetch_bytes.return_value = b"PK\x03\x04 epub bytes"
    assembler = MagicMock()
    pipeline = _pipeline(work, engine, assembler)

    pipeline.process_ref(WorkRef(id="10", source="opentextbooks"))

    assert pipeline.store.get("opentextbooks", "10") is work
    assert "epub" not in work.extra["unsupported_formats"]
    assembler.add_item_for.assert_called_once_with(
        path="Calculus.10.epub",
        content=b"PK\x03\x04 epub bytes",
        mimetype="application/epub+zip",
        is_front=False,
    )
