"""Tests for core.index_builder."""

from gutenberg2zim.core.index_builder import IndexBuilder
from gutenberg2zim.core.models import CollectionRef, Creator, Work
from gutenberg2zim.core.work_store import WorkStore


def _work(
    work_id: str,
    title: str,
    creators: list[Creator] | None = None,
    collections: list[CollectionRef] | None = None,
    popularity: int | None = None,
    description: str | None = None,
) -> Work:
    return Work(
        id=work_id,
        source="test",
        title=title,
        creators=creators or [],
        collections=collections or [],
        popularity=popularity,
        description=description,
    )


DICKENS = Creator(id="37", name="Charles Dickens")
AUSTEN = Creator(id="68", name="Jane Austen")
FICTION = CollectionRef(id="PR", name="English literature", kind="subject")
LCC_SHELF = CollectionRef(id="PR", name="English literature", kind="lcc_shelf")


def _store_with(*works: Work) -> WorkStore:
    store = WorkStore()
    for work in works:
        store.add(work)
    return store


def test_by_author_groups_works():
    store = _store_with(
        _work("1", "Bleak House", creators=[DICKENS]),
        _work("2", "Emma", creators=[AUSTEN]),
        _work("3", "David Copperfield", creators=[DICKENS]),
    )
    indexes = IndexBuilder(store).build(display_name="Test Source")
    assert [w.id for w in indexes.by_author["37"]] == ["1", "3"]
    assert [w.id for w in indexes.by_author["68"]] == ["2"]


def test_by_collection_groups_works():
    store = _store_with(
        _work("1", "Bleak House", collections=[FICTION]),
        _work("2", "Emma", collections=[FICTION]),
        _work("3", "No collection"),
    )
    indexes = IndexBuilder(store).build(display_name="Test Source")
    assert [w.id for w in indexes.by_collection["PR"]] == ["1", "2"]
    assert len(indexes.by_collection) == 1


def test_author_stats_count_and_popularity():
    store = _store_with(
        _work("1", "Bleak House", creators=[DICKENS], popularity=100),
        _work("2", "David Copperfield", creators=[DICKENS], popularity=50),
        # no popularity metric: counts as a work but adds nothing
        _work("3", "Mystery", creators=[DICKENS], popularity=None),
    )
    indexes = IndexBuilder(store).build(display_name="Test Source")
    assert indexes.author_stats["37"] == (3, 150)


def test_search_entries_for_works():
    store = _store_with(
        _work("1", "Bleak House", creators=[DICKENS], description="A novel."),
        _work("2", "Emma", creators=[AUSTEN]),
    )
    indexes = IndexBuilder(store).build(display_name="Test Source")
    entries = {entry.fname: entry for entry in indexes.search_entries}

    assert entries["book_1"].title == "Bleak House"
    assert entries["book_1"].route == "book/1"
    assert "A novel." in entries["book_1"].content
    assert "Charles Dickens" in entries["book_1"].content
    # falls back to a generic description mentioning the creator
    assert "Jane Austen" in entries["book_2"].content


def test_search_entries_for_collections():
    store = _store_with(
        _work("1", "Bleak House", creators=[DICKENS], collections=[LCC_SHELF]),
        _work("2", "Emma", creators=[AUSTEN], collections=[LCC_SHELF]),
    )
    indexes = IndexBuilder(store).build(display_name="Test Source")
    entries = {entry.fname: entry for entry in indexes.search_entries}

    entry = entries["collection_PR"]
    assert entry.title == "Collection PR"
    assert entry.route == "collections?collection=PR"
    assert "Collection PR" in entry.content
    assert "2 book(s)" in entry.content
    assert "Bleak House" in entry.content


def test_search_entries_encode_collection_ids_in_filenames_and_routes():
    collection = CollectionRef(
        id="Computer/Science & Maths#1?", name="Computer Science"
    )
    store = _store_with(_work("1", "Book", collections=[collection]))

    entries = {
        entry.fname: entry
        for entry in IndexBuilder(store).build(display_name="Test").search_entries
    }

    entry = entries["collection_Computer%2FScience%20%26%20Maths%231%3F"]
    assert (
        entry.route == "collections?collection=Computer%2FScience%20%26%20Maths%231%3F"
    )


def test_empty_store_builds_empty_indexes():
    indexes = IndexBuilder(WorkStore()).build(display_name="Test Source")
    assert indexes.authors == []
    assert indexes.by_author == {}
    assert indexes.by_collection == {}
    assert indexes.author_stats == {}
    # only the main listing pages get index entries
    assert [entry.fname for entry in indexes.search_entries] == [
        "books_list",
        "authors_list",
        "collections_list",
    ]
