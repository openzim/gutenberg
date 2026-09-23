"""Tests for sources.wikisource.resolver."""

from gutenberg2zim.core.models import Format, Work
from gutenberg2zim.sources.wikisource.resolver import WikisourceFormatResolver


def _work(*formats: Format) -> Work:
    return Work(
        id="en-abc123",
        source="wikisource",
        title="Some Book",
        formats=list(formats),
    )


def test_resolve_epub_uses_the_acquisition_link():
    work = _work(
        Format(
            name="epub",
            media_type="application/epub+zip",
            url="https://ws-export.wmcloud.org/?lang=en&format=epub&page=Some_Book",
        ),
        Format(
            name="html",
            media_type="application/xhtml+xml",
            url="https://ws-export.wmcloud.org/?lang=en&format=xhtml&page=Some_Book",
        ),
    )

    request = WikisourceFormatResolver().resolve(work, "epub")

    assert request is not None
    assert request.url.endswith("format=epub&page=Some_Book")
    assert request.format_name == "epub"


def test_resolve_returns_none_for_a_format_the_feed_does_not_advertise():
    work = _work(
        Format(
            name="epub",
            media_type="application/epub+zip",
            url="https://ws-export.wmcloud.org/?lang=en&format=epub&page=Some_Book",
        )
    )

    assert WikisourceFormatResolver().resolve(work, "pdf") is None


def test_resolve_returns_none_when_the_matching_format_has_no_url():
    work = _work(Format(name="epub", media_type="application/epub+zip", url=None))

    assert WikisourceFormatResolver().resolve(work, "epub") is None
