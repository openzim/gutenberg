"""Tests for sources.opentextbooks.resolver."""

from gutenberg2zim.core.models import Format, Work
from gutenberg2zim.sources.opentextbooks.resolver import (
    OpenTextbookLibraryFormatResolver,
)


def _work(*formats: Format) -> Work:
    return Work(
        id="10",
        source="opentextbooks",
        title="Calculus",
        formats=list(formats),
    )


def test_resolve_pdf_direct_file():
    work = _work(
        Format(name="PDF", media_type="application/pdf", url="https://a.org/book.pdf"),
        Format(name="Online", media_type="text/html", url="https://a.org/book"),
    )

    request = OpenTextbookLibraryFormatResolver().resolve(work, "pdf")

    assert request is not None
    assert request.url == "https://a.org/book.pdf"
    assert request.format_name == "pdf"
    assert request.extra["candidate_urls"] == ["https://a.org/book.pdf"]


def test_resolve_skips_landing_pages():
    """OTL links often point at HTML pages, not files: they are not usable"""
    work = _work(
        Format(
            name="PDF",
            media_type="application/pdf",
            url="https://biz.libretexts.org/Bookshelves/Accounting",
        )
    )

    assert OpenTextbookLibraryFormatResolver().resolve(work, "pdf") is None


def test_resolve_epub_uses_ebook_type():
    work = _work(
        Format(
            name="eBook",
            media_type="application/epub+zip",
            url="https://a.org/book.epub",
        )
    )

    request = OpenTextbookLibraryFormatResolver().resolve(work, "epub")

    assert request is not None
    assert request.url == "https://a.org/book.epub"


def test_resolve_html_uses_the_online_edition():
    work = _work(
        Format(name="Online", media_type="text/html", url="https://a.org/book")
    )

    request = OpenTextbookLibraryFormatResolver().resolve(work, "html")

    assert request is not None
    assert request.url == "https://a.org/book"


def test_resolve_extension_check_is_case_insensitive():
    work = _work(
        Format(name="PDF", media_type="application/pdf", url="https://a.org/BOOK.PDF")
    )

    assert OpenTextbookLibraryFormatResolver().resolve(work, "pdf") is not None


def test_resolve_unknown_format_returns_none():
    work = _work(
        Format(name="PDF", media_type="application/pdf", url="https://a.org/book.pdf")
    )

    assert OpenTextbookLibraryFormatResolver().resolve(work, "html") is None
