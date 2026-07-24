import gzip

from gutenberg2zim.csv_catalog import (
    CatalogEntry,
    filter_books,
    load_catalog,
    transform_locc_code,
)

CSV_CONTENT = """Text#,Type,Language,LoCC
84,Text,en,PR
11,Text,en;fr,PS
1089,Text,fr,QA
notanumber,Text,en,H
"""


def _write_catalog(tmp_path):
    csv_path = tmp_path / "pg_catalog.csv.gz"
    with gzip.open(csv_path, "wt", encoding="utf-8") as f:
        f.write(CSV_CONTENT)
    return csv_path


def test_load_catalog(tmp_path):
    catalog = load_catalog(_write_catalog(tmp_path))
    # the invalid book ID row is skipped
    assert len(catalog) == 3
    entry = next(e for e in catalog if e.book_id == 11)
    assert entry.languages == ["en", "fr"]
    assert entry.lcc_shelf == "PS"


def test_filter_books_no_filter():
    catalog = [
        CatalogEntry(book_id=84, languages=["en"], lcc_shelf="PR"),
        CatalogEntry(book_id=11, languages=["en", "fr"], lcc_shelf="PS"),
        CatalogEntry(book_id=1089, languages=["fr"], lcc_shelf="QA"),
    ]
    assert len(filter_books(catalog)) == 3


def test_filter_books_by_language(tmp_path):
    catalog = load_catalog(_write_catalog(tmp_path))
    filtered = filter_books(catalog, languages=["fr"])
    assert {e.book_id for e in filtered} == {11, 1089}


def test_filter_books_by_ids(tmp_path):
    catalog = load_catalog(_write_catalog(tmp_path))
    filtered = filter_books(catalog, only_books=[84])
    assert [e.book_id for e in filtered] == [84]


def test_filter_books_by_lcc_shelves(tmp_path):
    catalog = load_catalog(_write_catalog(tmp_path))
    filtered = filter_books(catalog, lcc_shelves=["PR"])
    assert [e.book_id for e in filtered] == [84]


def test_transform_locc_code():
    assert transform_locc_code("PR") == "PR"
    assert transform_locc_code("QA") == "Q"
    assert transform_locc_code("") == ""
    assert transform_locc_code("b123") == "B"
