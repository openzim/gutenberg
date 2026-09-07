"""Tests for source-neutral downloaded-content validation."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from gutenberg2zim.core.content_validation import is_html_document, is_valid_book_file


def _zip_bytes(*files: tuple[str, bytes]) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, content in files:
            archive.writestr(name, content)
    return output.getvalue()


@pytest.mark.parametrize(
    "content",
    [
        b"<!doctype html><html><body>Error</body></html>",
        b"  <html><body>Access denied</body></html>",
        b"<head><title>Not found</title></head>",
    ],
)
def test_is_html_document_detects_html_error_pages(content: bytes):
    assert is_html_document(content)


def test_empty_content_is_invalid_for_book_formats():
    assert not is_valid_book_file(b"", "pdf")
    assert not is_valid_book_file(b"", "epub")


def test_pdf_validation_uses_file_signature_not_content_type():
    assert is_valid_book_file(b"%PDF-1.7\ncontent", "pdf")
    assert not is_valid_book_file(b"not a pdf", "pdf")


def test_html_error_page_is_rejected_even_when_format_is_pdf():
    assert not is_valid_book_file(
        b"<!doctype html><html><body>Temporary error</body></html>", "pdf"
    )


def test_epub_validation_accepts_a_valid_zip_container():
    epub = _zip_bytes(("mimetype", b"application/epub+zip"))
    assert is_valid_book_file(epub, "epub")


def test_epub_validation_rejects_signature_only_data():
    assert not is_valid_book_file(b"PK\x03\x04", "epub")


def test_epub_validation_rejects_arbitrary_non_epub_binary():
    arbitrary_zip = _zip_bytes(("README.txt", b"not an ebook"))
    assert not is_valid_book_file(arbitrary_zip, "epub")


def test_epub_validation_rejects_corrupt_zip_data():
    valid_zip = _zip_bytes(("mimetype", b"application/epub+zip"))
    assert not is_valid_book_file(valid_zip[:-4], "epub")


def test_unknown_format_is_rejected():
    assert not is_valid_book_file(b"some content", "mobi")
