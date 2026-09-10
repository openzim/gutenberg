"""Validation helpers for downloaded source content."""

from io import BytesIO
from zipfile import BadZipFile, ZipFile


def is_html_document(content: bytes) -> bool:
    """Return whether downloaded content looks like an HTML document."""
    stripped = content.lstrip().lower()
    return stripped.startswith((b"<!doctype html", b"<html", b"<head", b"<body"))


def is_valid_book_file(content: bytes, format_name: str) -> bool:
    """Validate downloaded content independently of its HTTP metadata."""
    if not content or is_html_document(content):
        return False
    if format_name == "pdf":
        return content.lstrip().startswith(b"%PDF-")
    if format_name == "epub":
        try:
            with ZipFile(BytesIO(content)) as archive:
                if archive.testzip() is not None:
                    return False
                try:
                    mimetype = archive.read("mimetype")
                except KeyError:
                    return False
                return mimetype == b"application/epub+zip"
        except BadZipFile:
            return False
    return False
