"""Tests for generic (format-level) cover extraction."""

import io
import zipfile

from gutenberg2zim.core.covers import _epub_cover, extract_cover


def test_extract_cover_returns_none_for_unsupported_format():
    assert extract_cover(b"whatever", "txt") is None


def test_epub_cover_decodes_manifest_href_before_archive_lookup():
    epub = io.BytesIO()
    with zipfile.ZipFile(epub, "w") as archive:
        archive.writestr(
            "META-INF/container.xml",
            """<container><rootfiles><rootfile full-path="OPS/package.opf"/>
            </rootfiles></container>""",
        )
        archive.writestr(
            "OPS/package.opf",
            """<package><metadata><meta name="cover" content="cover"/>
            </metadata><manifest><item id="cover" href="cover%20image.jpg"
            media-type="image/jpeg"/></manifest></package>""",
        )
        archive.writestr("OPS/cover image.jpg", b"cover image")

    assert _epub_cover(epub.getvalue()) == b"cover image"
