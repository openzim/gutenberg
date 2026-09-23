"""Tests for OPDS-backed Wikisource discovery."""

import re

import pytest

from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.ports import CatalogFilters
from gutenberg2zim.core.utils import CriticalError
from gutenberg2zim.sources.wikisource.catalog import (
    WIKISOURCE_SOURCE,
    WikisourceCatalog,
)

BASE = "https://ws-export.wmcloud.org"

INDEX_HTML = """<html><body><h1>Index of /opds/en</h1>
<a href="/opds/">Parent Directory</a>
<a href="Ready_for_export.xml">Ready_for_export.xml</a>
</body></html>"""


def _entry(page: str, title: str, *, epub: bool = True, xhtml: bool = True) -> str:
    links = ""
    if epub:
        links += (
            '<link rel="http://opds-spec.org/acquisition" '
            'type="application/epub+zip" '
            f'href="{BASE}/?lang=en&amp;format=epub&amp;page={page}"/>'
        )
    if xhtml:
        links += (
            '<link rel="http://opds-spec.org/acquisition" '
            'type="application/xhtml+xml" '
            f'href="{BASE}/?lang=en&amp;format=xhtml&amp;page={page}"/>'
        )
    return (
        '<entry xml:lang="en">'
        f"<title>{title}</title>"
        f'<id xsi:type="dcterms:URI">https://en.wikisource.org/wiki/{page}</id>'
        "<rights>http://creativecommons.org/licenses/by-sa/3.0</rights>"
        "<author><name>A. Writer</name></author>"
        '<dc:language xsi:type="dcterms:RFC4646">en</dc:language>'
        f'<dc:source xsi:type="dcterms:URI">https://en.wikisource.org/wiki/{page}</dc:source>'
        '<dcterms:issued xsi:type="dcterms:W3CDTF">1913</dcterms:issued>'
        f"{links}"
        "</entry>"
    )


def _feed(*entries: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/">'
        "<title>Category:Ready_for_export</title>"
        f"{''.join(entries)}"
        "</feed>"
    )


class StubEngine(DownloadEngine):
    def __init__(self, responses: dict[str, str]):
        self._responses = responses
        self.fetched: list[str] = []

    def fetch_bytes(self, url: str) -> bytes:
        self.fetched.append(url)
        for fragment, body in self._responses.items():
            if fragment in url:
                return body.encode("utf-8")
        raise AssertionError(f"unexpected fetch: {url}")


def _catalog(feed_body: str) -> tuple[WikisourceCatalog, StubEngine]:
    engine = StubEngine(
        {"/opds/en/Ready_for_export.xml": feed_body, "/opds/en/": INDEX_HTML}
    )
    return WikisourceCatalog(engine, base_url=BASE), engine


def test_discover_parses_feed_entries_into_work_refs():
    catalog, _ = _catalog(
        _feed(
            _entry("First_Book", "First Book"),
            _entry("Second_Book", "Second Book", xhtml=False),
        )
    )

    refs = list(catalog.discover(CatalogFilters(languages=["en"])))

    assert len(refs) == 2
    first = refs[0]
    assert first.source == WIKISOURCE_SOURCE
    assert first.extra["title"] == "First Book"
    assert first.extra["language"] == "en"
    assert first.extra["license"] == "http://creativecommons.org/licenses/by-sa/3.0"
    assert first.extra["author"] == "A. Writer"
    assert first.extra["issued"] == "1913"
    assert first.extra["source_url"] == "https://en.wikisource.org/wiki/First_Book"
    formats = {name: url for name, _mt, url in first.extra["formats"]}
    assert "epub" in formats
    assert formats["epub"].endswith("format=epub&page=First_Book")
    assert "xhtml" in formats
    # second book advertises epub only
    assert [name for name, _mt, _url in refs[1].extra["formats"]] == ["epub"]


def test_discover_mints_path_safe_unique_ids():
    catalog, _ = _catalog(
        _feed(
            _entry("%27Tis_Sixty_Years_Since", chr(0x2019) + "Tis Sixty Years Since"),
            _entry("War_and_Peace/Chapter_1", "War and Peace"),
        )
    )

    refs = list(catalog.discover(CatalogFilters(languages=["en"])))

    ids = [ref.id for ref in refs]
    assert len(set(ids)) == len(ids)
    for work_id in ids:
        assert re.fullmatch(r"[a-z0-9_-]+", work_id), work_id
        assert work_id.startswith("en_")


def test_discover_requires_at_least_one_language():
    catalog, _ = _catalog(_feed(_entry("First_Book", "First Book")))

    with pytest.raises(CriticalError):
        list(catalog.discover(CatalogFilters()))


def test_discover_filters_out_entries_without_a_requested_format():
    catalog, _ = _catalog(_feed(_entry("First_Book", "First Book")))

    assert (
        list(catalog.discover(CatalogFilters(languages=["en"], formats=["pdf"]))) == []
    )


def test_discover_selects_by_catalog_position():
    catalog, _ = _catalog(
        _feed(
            _entry("First_Book", "First Book"),
            _entry("Second_Book", "Second Book"),
            _entry("Third_Book", "Third Book"),
        )
    )

    refs = list(catalog.discover(CatalogFilters(languages=["en"], book_ids=["2"])))

    assert [ref.extra["title"] for ref in refs] == ["Second Book"]
