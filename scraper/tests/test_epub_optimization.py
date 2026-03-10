"""Tests for EPUB optimization functions in export.py."""

from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup

from gutenberg2zim.export import _process_epub_html, _process_epub_ncx

# Test data for NCX processing
NCX_WITH_LICENSE = b"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <navMap>
    <navPoint id="np1"><navLabel><text>Chapter 1</text></navLabel></navPoint>
    <navPoint id="np2"><navLabel><text>Chapter 2</text></navLabel></navPoint>
    <navPoint id="np3"><navLabel><text>*** START: FULL LICENSE ***</text></navLabel>
    </navPoint>
    <navPoint id="np4"><navLabel><text>License section</text></navLabel></navPoint>
  </navMap>
</ncx>"""

NCX_WITHOUT_LICENSE = b"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <navMap>
    <navPoint id="np1"><navLabel><text>Chapter 1</text></navLabel></navPoint>
    <navPoint id="np2"><navLabel><text>Chapter 2</text></navLabel></navPoint>
  </navMap>
</ncx>"""

# Test data for HTML processing
HTML_WITH_LICENSE = b"""<html><body>
<p>Gutenberg preamble (boilerplate)</p>
<p>*** START OF THE PROJECT GUTENBERG EBOOK The Book</p>
<p>Actual book content</p>
<p>*** END OF THE PROJECT GUTENBERG EBOOK The Book</p>
<p>Gutenberg postamble (boilerplate)</p>
</body></html>"""

HTML_WITHOUT_MARKERS = b"""<html><body>
<p>Book content only, no markers</p>
</body></html>"""

HTML_WITH_CHARSET_META = b"""<html><head><meta charset="utf-8" /></head>
<body><p>Content</p></body></html>"""

HTML_WITH_IMG_SRC = b"""<html><body>
<img src="images/foo.jpg" alt="test" />
</body></html>"""


class TestProcessEpubNcx:
    """Test NCX file processing (_process_epub_ncx).

    Note: The license section removal logic is kept for compatibility with
    older EPUB files that may contain Gutenberg license markers in the NCX.
    However, we don't have real examples of such files. When found, the app
    will log the book ID for investigation (logger.info in _process_epub_ncx).
    """

    # TODO: Enable this test if/when we find a real EPUB with license in NCX
    # def test_process_epub_ncx_removes_license_section(self):
    #     """Verify that license section starting at marker is removed."""
    #     result = _process_epub_ncx(NCX_WITH_LICENSE)
    #     soup = BeautifulSoup(result, "lxml-xml")
    #
    #     # np3 and following elements should be removed
    #     assert soup.find("navPoint", {"id": "np3"}) is None
    #     # np1 and np2 should remain
    #     assert soup.find("navPoint", {"id": "np1"}) is not None
    #     assert soup.find("navPoint", {"id": "np2"}) is not None

    def test_process_epub_ncx_no_license_unchanged(self):
        """Verify that NCX without license markers is unchanged."""
        result = _process_epub_ncx(NCX_WITHOUT_LICENSE)
        soup = BeautifulSoup(result, "lxml-xml")

        # All navPoints should remain
        assert soup.find("navPoint", {"id": "np1"}) is not None
        assert soup.find("navPoint", {"id": "np2"}) is not None

    def test_process_epub_ncx_returns_bytes(self):
        """Verify that result is bytes."""
        result = _process_epub_ncx(NCX_WITHOUT_LICENSE)
        assert isinstance(result, bytes)


class TestProcessEpubHtml:
    """Test HTML file processing (_process_epub_html)."""

    @pytest.fixture
    def book_stub(self):
        """Create minimal book stub for HTML processing."""
        return SimpleNamespace(
            book_id=12345,
            title="Test Book",
            author=SimpleNamespace(name=lambda: "Test Author"),
        )

    def test_process_epub_html_removes_preamble_and_postamble(self, book_stub):
        """Verify that Gutenberg preamble and postamble are removed."""
        result = _process_epub_html(HTML_WITH_LICENSE, book_stub)
        result_str = result.decode("utf-8")

        # Preamble and postamble should be removed
        assert "Gutenberg preamble" not in result_str
        assert "Gutenberg postamble" not in result_str

        # Book content should remain
        assert "Actual book content" in result_str

    def test_process_epub_html_no_markers_unchanged(self, book_stub):
        """Verify that HTML without markers is preserved."""
        result = _process_epub_html(HTML_WITHOUT_MARKERS, book_stub)
        result_str = result.decode("utf-8")

        assert "Book content only, no markers" in result_str

    def test_process_epub_html_removes_charset_meta(self, book_stub):
        """Verify that charset meta tag is removed."""
        result = _process_epub_html(HTML_WITH_CHARSET_META, book_stub)
        result_str = result.decode("utf-8")

        # charset meta should be removed by update_html_for_static
        assert 'charset="utf-8"' not in result_str

    def test_process_epub_html_no_img_rewrite(self, book_stub):
        """Verify that img src is not rewritten for EPUB (epub=True)."""
        result = _process_epub_html(HTML_WITH_IMG_SRC, book_stub)
        result_str = result.decode("utf-8")

        # img src should NOT be rewritten (epub=True skips this)
        assert "images/foo.jpg" in result_str

    def test_process_epub_html_returns_bytes(self, book_stub):
        """Verify that result is bytes."""
        result = _process_epub_html(HTML_WITH_LICENSE, book_stub)
        assert isinstance(result, bytes)
