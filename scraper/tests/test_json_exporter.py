"""Tests for core.exporters.json_exporter with a mocked assembler (no ZIM)."""

from unittest.mock import MagicMock

from gutenberg2zim.core.exporters.json_exporter import generate_json_files
from gutenberg2zim.core.index_builder import IndexBuilder
from gutenberg2zim.core.models import CollectionRef, Creator, Work
from gutenberg2zim.core.work_store import WorkStore


def _indexes(store: WorkStore, *, add_lcc_shelves: bool):
    return IndexBuilder(store).build(
        add_lcc_shelves=add_lcc_shelves, display_name="Test Source"
    )


def _work(work_id: str, title: str, creator: Creator, shelf: str) -> Work:
    return Work(
        id=work_id,
        source="gutenberg",
        title=title,
        creators=[creator],
        languages=["en"],
        collections=[CollectionRef(id=shelf, name=shelf, kind="lcc_shelf")],
        popularity=1,
        extra={"downloads": 100, "has_cover": False},
    )


def _store() -> WorkStore:
    dickens = Creator(id="37", name="Charles Dickens")
    austen = Creator(id="68", name="Jane Austen")
    store = WorkStore()
    store.add(_work("1", "Bleak House", dickens, "PR"))
    store.add(_work("2", "Emma", austen, "PR"))
    store.add(_work("3", "Oliver Twist", dickens, "PR"))
    return store


def _added_paths(assembler: MagicMock) -> set[str]:
    return {call.kwargs["path"] for call in assembler.add_item_for.call_args_list}


def test_generate_json_files_with_lcc_shelves():
    """The --lcc-shelves path must complete and emit shelf JSON files"""
    assembler = MagicMock(name="assembler")

    store = _store()
    generate_json_files(
        zim_name="test",
        formats=["epub", "html"],
        work_store=store,
        assembler=assembler,
        add_lcc_shelves=True,
        display_name="Test Source",
        indexes=_indexes(store, add_lcc_shelves=True),
    )

    paths = _added_paths(assembler)
    assert "books.json" in paths
    assert "authors.json" in paths
    assert "lcc_shelves.json" in paths
    assert "lcc_shelves/PR.json" in paths
    # per-book and per-author detail files
    assert "books/1.json" in paths
    assert "authors/37.json" in paths


def test_generate_json_files_without_lcc_shelves():
    assembler = MagicMock(name="assembler")

    store = _store()
    generate_json_files(
        zim_name="test",
        formats=["html"],
        work_store=store,
        assembler=assembler,
        add_lcc_shelves=False,
        display_name="Test Source",
        indexes=_indexes(store, add_lcc_shelves=False),
    )

    paths = _added_paths(assembler)
    assert "books.json" in paths
    assert "lcc_shelves.json" not in paths
    assert not any(path.startswith("lcc_shelves/") for path in paths)
