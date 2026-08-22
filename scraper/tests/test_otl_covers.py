"""Tests for Open Textbook Library cover extraction."""

import io
import zipfile

from gutenberg2zim.sources.opentextbooks.covers import _epub_cover, fetch_page_cover


class StubEngine:
    def __init__(self):
        self.pages = {
            "https://example.org/book.html": (
                b'<meta property="og:image" content="/cover.png">'
            ),
            "https://example.org/cover.png": b"image bytes",
        }

    def fetch_bytes(self, url: str) -> bytes:
        return self.pages[url]


def test_fetch_page_cover_falls_back_to_open_graph_image(monkeypatch):
    monkeypatch.setattr(
        "gutenberg2zim.sources.opentextbooks.covers.ImageProcessor.optimize_image_content",
        lambda content: b"webp:" + content,
    )

    cover = fetch_page_cover(StubEngine(), "https://example.org/book")

    assert cover == b"webp:image bytes"


def test_fetch_page_cover_prefers_portrait_book_cover(monkeypatch):
    engine = StubEngine()
    engine.pages["https://example.org/book.html"] = (
        b'<meta property="og:image" content="/social-card.png">'
        b'<img class="cover" src="/book-cover.png">'
    )
    engine.pages["https://example.org/social-card.png"] = b"social"
    engine.pages["https://example.org/book-cover.png"] = b"book"
    monkeypatch.setattr(
        "gutenberg2zim.sources.opentextbooks.covers.ImageProcessor.optimize_image_content",
        lambda content: b"webp:" + content,
    )

    cover = fetch_page_cover(engine, "https://example.org/book")

    assert cover == b"webp:book"


def test_fetch_page_cover_returns_none_without_a_source_url():
    assert fetch_page_cover(StubEngine(), None) is None


def test_fetch_page_cover_returns_none_when_page_has_no_image():
    engine = StubEngine()
    engine.pages["https://example.org/book.html"] = b"<html><body>Book</body></html>"

    assert fetch_page_cover(engine, "https://example.org/book") is None


def test_fetch_page_cover_returns_none_when_fetch_fails():
    assert (
        fetch_page_cover(StubEngine(), "https://example.org/missing") is None
    )  # type: ignore[arg-type]


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
