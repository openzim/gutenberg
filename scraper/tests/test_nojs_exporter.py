"""Tests for No-JS fallback page generation."""

from unittest.mock import MagicMock

from gutenberg2zim.core.exporters.nojs_exporter import generate_noscript_pages
from gutenberg2zim.core.index_builder import IndexBuilder
from gutenberg2zim.core.models import CollectionRef, Creator, Work
from gutenberg2zim.core.work_store import WorkStore


def _item_call(assembler: MagicMock, path: str):
    return next(
        call
        for call in assembler.add_item_for.call_args_list
        if call.kwargs["path"] == path
    )


def test_collection_pages_use_configured_label_and_collection_name():
    assembler = MagicMock(name="assembler")
    store = WorkStore()
    store.add(
        Work(
            id="42",
            source="opentextbooks",
            title="Book",
            creators=[Creator(id="1", name="Author")],
            collections=[CollectionRef(id="Computer/Science", name="Computer Science")],
        )
    )

    generate_noscript_pages(
        formats=["pdf"],
        work_store=store,
        assembler=assembler,
        display_name="Open Textbook Library",
        collection_label="Subjects",
        indexes=IndexBuilder(store).build(display_name="Open Textbook Library"),
    )

    listing = _item_call(assembler, "noscript/collections.html").kwargs
    detail = _item_call(assembler, "noscript/collection_Computer%2FScience.html").kwargs
    assert "Subjects" in listing["content"]
    assert "Computer Science" in listing["content"]
    assert 'name="viewport"' in listing["content"]
    assert listing["title"] == "Subjects - Open Textbook Library"
    assert "Subjects: Computer Science" in detail["content"]
    assert 'name="viewport"' in detail["content"]
    assert detail["title"] == "Subjects: Computer Science"
    assert "collection_Computer%2FScience.html" in listing["content"]


def test_book_format_links_are_url_encoded():
    assembler = MagicMock(name="assembler")
    store = WorkStore()
    store.add(
        Work(
            id="11",
            source="gutenberg",
            title="Alice's Adventures in Wonderland",
            creators=[Creator(id="1", name="Lewis Carroll")],
        )
    )

    generate_noscript_pages(
        formats=["html", "epub", "pdf"],
        work_store=store,
        assembler=assembler,
        display_name="Project Gutenberg",
        indexes=IndexBuilder(store).build(display_name="Project Gutenberg"),
    )

    page = _item_call(assembler, "noscript/book_11.html").kwargs["content"]
    assert "Alice%27s%20Adventures%20in%20Wonderland.11" in page
    assert "Alice%27s%20Adventures%20in%20Wonderland.11.epub" in page
    assert "Alice%27s%20Adventures%20in%20Wonderland.11.pdf" in page


def test_author_page_renders_bio_portrait_and_wikipedia_link():
    assembler = MagicMock(name="assembler")
    creator = Creator(
        id="68",
        name="Jane Austen",
        extra={
            "webpage_resource": "https://en.wikipedia.org/wiki/Jane_Austen",
            "bio": "An English novelist.",
            "portrait_path": "authors/68.webp",
        },
    )
    store = WorkStore()
    store.add(Work(id="1", source="gutenberg", title="Emma", creators=[creator]))

    generate_noscript_pages(
        formats=["html"],
        work_store=store,
        assembler=assembler,
        display_name="Project Gutenberg",
        indexes=IndexBuilder(store).build(display_name="Project Gutenberg"),
    )

    page = _item_call(assembler, "noscript/author_68.html").kwargs["content"]
    assert "authors/68.webp" in page
    assert "An English novelist." in page
    assert "en.wikipedia.org/wiki/Jane_Austen" in page
