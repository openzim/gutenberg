"""Tests for CSV-backed Open Textbook Library discovery."""

from pathlib import Path

from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.ports import CatalogFilters
from gutenberg2zim.sources.opentextbooks.catalog import (
    CATALOG_FILENAME,
    OTL_SOURCE,
    OpenTextbookLibraryCatalog,
)

BASE = "https://open.umn.edu/opentextbooks"
CSV_HEADER = "Otl id,Title,Type 1,URL 1,Type 2,URL 2\n"


class StubEngine(DownloadEngine):
    def __init__(self):
        self.downloaded: list[str] = []

    def download(self, request, dest=None):
        self.downloaded.append(request.url)
        assert dest is not None
        dest.write_text(CSV_HEADER, encoding="utf-8")

    def fetch_bytes(self, url):
        self.downloaded.append(url)
        return CSV_HEADER.encode("utf-8")


def _catalog(
    tmp_path: Path, rows: list[str]
) -> tuple[OpenTextbookLibraryCatalog, StubEngine]:
    csv_path = tmp_path / CATALOG_FILENAME
    csv_path.write_text(CSV_HEADER + "\n".join(rows) + "\n", encoding="utf-8")
    engine = StubEngine()
    return OpenTextbookLibraryCatalog(engine, cache_dir=tmp_path), engine


def test_discover_uses_cached_csv_and_selects_downloadable_books(tmp_path):
    catalog, engine = _catalog(
        tmp_path,
        [
            "10,Landing page,PDF,https://example.org/landing,,",
            "20,Direct PDF,PDF,https://example.org/book.pdf,,",
            "30,Direct EPUB,eBook,https://example.org/book.epub,,",
        ],
    )

    refs = list(catalog.discover(CatalogFilters()))

    assert [ref.id for ref in refs] == ["20", "30"]
    assert all(ref.source == OTL_SOURCE for ref in refs)
    assert engine.downloaded == []


def test_discover_selects_downloadable_catalog_positions(tmp_path):
    catalog, _ = _catalog(
        tmp_path,
        [
            "10,Landing page,PDF,https://example.org/landing,,",
            "20,First PDF,PDF,https://example.org/one.pdf,,",
            "30,Second PDF,PDF,https://example.org/two.pdf,,",
        ],
    )

    refs = list(catalog.discover(CatalogFilters(book_ids=["1", "2"], formats=["pdf"])))

    assert [ref.id for ref in refs] == ["20", "30"]


def test_discover_does_not_select_online_editions_for_html_only_requests(tmp_path):
    catalog, _ = _catalog(
        tmp_path,
        ["10,Online edition,Online,https://example.org/book,,"],
    )

    assert list(catalog.discover(CatalogFilters(formats=["html"]))) == []


def test_discover_filters_by_case_insensitive_subject_name(tmp_path):
    csv_path = tmp_path / CATALOG_FILENAME
    csv_path.write_text(
        "Otl id,Title,Subject 1,Subject 2,Type 1,URL 1\n"
        "10,Algebra,Mathematics - Algebra,Mathematics - Pure,PDF,https://example.org/a.pdf\n"
        "20,Economics,Economics,Business,PDF,https://example.org/e.pdf\n",
        encoding="utf-8",
    )
    catalog = OpenTextbookLibraryCatalog(StubEngine(), cache_dir=tmp_path)

    refs = list(
        catalog.discover(
            CatalogFilters(options={"subjects": ["mathematics - algebra"]})
        )
    )

    assert [ref.id for ref in refs] == ["10"]


def test_discover_selects_exact_otl_ids(tmp_path):
    catalog, _ = _catalog(
        tmp_path,
        [
            "10,First PDF,PDF,https://example.org/one.pdf,,",
            "20,Second PDF,PDF,https://example.org/two.pdf,,",
        ],
    )

    refs = list(catalog.discover(CatalogFilters(options={"book_ids": ["20"]})))

    assert [ref.id for ref in refs] == ["20"]


def test_list_subjects_returns_unique_sorted_subjects(tmp_path):
    csv_path = tmp_path / CATALOG_FILENAME
    csv_path.write_text(
        "Otl id,Title,Subject 1,Subject 2,Type 1,URL 1\n"
        "10,Algebra,Mathematics - Algebra,Mathematics - Pure,PDF,https://example.org/a.pdf\n"
        "20,Economics,Economics,Mathematics - Pure,PDF,https://example.org/e.pdf\n",
        encoding="utf-8",
    )
    catalog = OpenTextbookLibraryCatalog(StubEngine(), cache_dir=tmp_path)

    assert catalog.list_subjects() == [
        "Economics",
        "Mathematics - Algebra",
        "Mathematics - Pure",
    ]


def test_discover_reads_numbered_columns_beyond_previous_limits(tmp_path):
    csv_path = tmp_path / CATALOG_FILENAME
    csv_path.write_text(
        "Otl id,Title,Subject 1,Subject 3,Type 1,URL 1,Type 7,URL 7\n"
        "10,Advanced,Mathematics,Physics,,,PDF,https://example.org/book.pdf\n",
        encoding="utf-8",
    )
    catalog = OpenTextbookLibraryCatalog(StubEngine(), cache_dir=tmp_path)

    (ref,) = catalog.discover(CatalogFilters(formats=["pdf"]))

    assert ref.id == "10"
    assert ref.extra["subjects"] == ("Mathematics", "Physics")
    assert ref.extra["formats"] == (("PDF", "https://example.org/book.pdf"),)


def test_refresh_catalog_downloads_even_when_cache_exists(tmp_path):
    _, engine = _catalog(tmp_path, [])
    catalog = OpenTextbookLibraryCatalog(
        engine, cache_dir=tmp_path, refresh_catalog=True
    )

    catalog.refresh()

    assert engine.downloaded == [f"{BASE}/download.csv"]


def test_discover_downloads_csv_when_cache_is_missing(tmp_path):
    engine = StubEngine()
    catalog = OpenTextbookLibraryCatalog(engine, cache_dir=tmp_path)

    assert list(catalog.discover(CatalogFilters())) == []
    assert engine.downloaded == [f"{BASE}/download.csv"]


def test_discover_keeps_catalog_in_memory_without_a_cache_dir():
    engine = StubEngine()
    catalog = OpenTextbookLibraryCatalog(engine)

    assert list(catalog.discover(CatalogFilters())) == []
    assert engine.downloaded == [f"{BASE}/download.csv"]
