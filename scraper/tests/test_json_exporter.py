"""Tests for core.exporters.json_exporter with a mocked assembler (no ZIM)."""

import json
from unittest.mock import MagicMock

from gutenberg2zim.core.exporters.json_exporter import generate_json_files
from gutenberg2zim.core.index_builder import IndexBuilder
from gutenberg2zim.core.models import CollectionRef, Creator, Work
from gutenberg2zim.core.work_store import WorkStore


def _indexes(store: WorkStore):
    return IndexBuilder(store).build(display_name="Test Source")


def _work(work_id: str, title: str, creator: Creator, shelf: str) -> Work:
    return Work(
        id=work_id,
        source="gutenberg",
        title=title,
        creators=[creator],
        languages=["en"],
        collections=[CollectionRef(id=shelf, name=shelf, kind="lcc_shelf")],
        popularity=1,
        primary_metric=100,
        extra={"has_cover": False},
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


def _config_content(assembler: MagicMock) -> dict:
    call = next(
        call
        for call in assembler.add_item_for.call_args_list
        if call.kwargs["path"] == "config.json"
    )
    return json.loads(call.kwargs["content"])


def test_generate_json_files_emits_collections():
    assembler = MagicMock(name="assembler")

    store = _store()
    generate_json_files(
        zim_name="test",
        formats=["epub", "html"],
        work_store=store,
        assembler=assembler,
        display_name="Test Source",
        indexes=_indexes(store),
    )

    paths = _added_paths(assembler)
    assert "books.json" in paths
    assert "authors.json" in paths
    assert "collections.json" in paths
    assert "collections/PR.json" in paths
    # per-book and per-author detail files
    assert "books/1.json" in paths
    assert "authors/37.json" in paths


def test_generate_json_files_does_not_emit_legacy_shelf_files():
    assembler = MagicMock(name="assembler")

    store = _store()
    generate_json_files(
        zim_name="test",
        formats=["html"],
        work_store=store,
        assembler=assembler,
        display_name="Test Source",
        indexes=_indexes(store),
    )

    paths = _added_paths(assembler)
    assert "books.json" in paths
    assert "lcc_shelves.json" not in paths
    assert not any(path.startswith("lcc_shelves/") for path in paths)


def test_collection_detail_path_encodes_unsafe_collection_id():
    assembler = MagicMock(name="assembler")
    creator = Creator(id="1", name="Author")
    store = WorkStore()
    store.add(_work("1", "Book", creator, "A/B & C"))

    generate_json_files(
        zim_name="test",
        formats=["html"],
        work_store=store,
        assembler=assembler,
        display_name="Test Source",
        indexes=_indexes(store),
    )

    assert "collections/A%2FB%20%26%20C.json" in _added_paths(assembler)


def test_config_includes_source_theme_and_features():
    assembler = MagicMock(name="assembler")
    store = _store()

    generate_json_files(
        zim_name="test",
        formats=["epub", "pdf"],
        work_store=store,
        assembler=assembler,
        display_name="Open Textbook Library",
        source_slug="opentextbooks",
        source_description="Free textbooks.",
        collection_label="Subjects",
        collection_icon_style="subject",
        indexes=_indexes(store),
    )

    config = _config_content(assembler)
    assert config["source"] == {
        "slug": "opentextbooks",
        "name": "Open Textbook Library",
        "description": "Free textbooks.",
    }
    assert config["theme"]["formatIcons"] == {"epub": "epub", "pdf": "pdf"}
    assert config["theme"]["routeLabels"]["collections"] == "Subjects"
    assert config["theme"]["collectionIconStyle"] == "subject"
    assert config["features"] == {
        "epubReader": True,
        "pdfReader": True,
        "noscriptFallback": True,
    }


def test_config_only_advertises_enabled_readers():
    assembler = MagicMock(name="assembler")
    store = _store()

    generate_json_files(
        zim_name="test",
        formats=["html"],
        work_store=store,
        assembler=assembler,
        display_name="Test Source",
        indexes=_indexes(store),
    )

    assert _config_content(assembler)["features"] == {
        "epubReader": False,
        "pdfReader": False,
        "noscriptFallback": True,
    }


def test_book_detail_exports_source_defined_primary_metric():
    assembler = MagicMock(name="assembler")
    creator = Creator(id="1", name="Reviewer")
    store = WorkStore()
    store.add(
        Work(
            id="10",
            source="opentextbooks",
            title="Reviewed Textbook",
            creators=[creator],
            primary_metric=7,
        )
    )

    generate_json_files(
        zim_name="test",
        formats=["pdf"],
        work_store=store,
        assembler=assembler,
        display_name="Open Textbook Library",
        source_slug="opentextbooks",
        indexes=_indexes(store),
    )

    detail_call = next(
        call
        for call in assembler.add_item_for.call_args_list
        if call.kwargs["path"] == "books/10.json"
    )
    assert json.loads(detail_call.kwargs["content"])["primaryMetric"] == 7
