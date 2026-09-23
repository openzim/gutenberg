"""Tests for sources.wikisource.metadata."""

from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.sources.wikisource.metadata import WikisourceMetadata


class StubEngine(DownloadEngine):
    def __init__(self):
        pass


def _ref() -> WorkRef:
    return WorkRef(
        id="en_first-book-12345678",
        source="wikisource",
        extra={
            "title": "First Book",
            "author": "A. Writer",
            "language": "en",
            "license": "http://creativecommons.org/licenses/by-sa/3.0",
            "source_url": "https://en.wikisource.org/wiki/First_Book",
            "issued": "1913",
            "page": "First_Book",
            "lang": "en",
            "formats": [
                (
                    "epub",
                    "application/epub+zip",
                    "https://ws-export.wmcloud.org/?lang=en&format=epub&page=First_Book",
                ),
                (
                    "xhtml",
                    "application/xhtml+xml",
                    "https://ws-export.wmcloud.org/?lang=en&format=xhtml&page=First_Book",
                ),
            ],
        },
    )


def _metadata() -> WikisourceMetadata:
    return WikisourceMetadata("https://ws-export.wmcloud.org", engine=StubEngine())


def test_fetch_maps_the_feed_entry_into_a_work():
    (work,) = list(_metadata().fetch([_ref()]))

    assert work.id == "en_first-book-12345678"
    assert work.source == "wikisource"
    assert work.title == "First Book"
    assert work.languages == ["en"]
    assert work.license == "http://creativecommons.org/licenses/by-sa/3.0"
    assert work.source_url == "https://en.wikisource.org/wiki/First_Book"
    assert [creator.name for creator in work.creators] == ["A. Writer"]
    assert {fmt.name for fmt in work.formats} == {"epub", "xhtml"}
    epub = next(fmt for fmt in work.formats if fmt.name == "epub")
    assert epub.media_type == "application/epub+zip"
    assert epub.url is not None
    assert epub.url.endswith("format=epub&page=First_Book")


def test_fetch_gives_the_same_author_id_for_the_same_name():
    ref_one = _ref()
    ref_two = _ref()
    ref_two.extra["title"] = "Second Book"

    works = list(_metadata().fetch([ref_one, ref_two]))

    assert works[0].creators[0].id == works[1].creators[0].id


def test_fetch_tolerates_a_missing_author():
    ref = _ref()
    ref.extra["author"] = None

    (work,) = list(_metadata().fetch([ref]))

    assert work.creators == []
