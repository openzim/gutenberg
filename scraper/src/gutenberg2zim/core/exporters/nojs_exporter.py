"""No-JavaScript fallback HTML pages exporter (moved from `gutenberg2zim.export`).

Renders the `noscript/` Jinja templates so the ZIM remains browsable when
the Vue.js UI cannot run. Owns the shared `jinja_env` and its filters.
"""

import urllib.parse
from importlib import resources

from jinja2 import Environment, PackageLoader, select_autoescape

from gutenberg2zim.constants import logger
from gutenberg2zim.core.index_builder import Indexes
from gutenberg2zim.core.language import language_name
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.utils import (
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    collection_key,
    creator_template_context,
    work_template_context,
)
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler

jinja_env = Environment(
    loader=PackageLoader("gutenberg2zim", "templates"),
    autoescape=select_autoescape(("html", "htm", "xml")),
)


def fa_for_format(book_format):
    return {
        "html": "",
        "info": "fa-info-circle",
        "epub": "fa-download",
        "pdf": "fa-file-pdf-o",
    }.get(book_format, "fa-file-o")


def zim_link_prefix(book_format):
    return "../{}/".format({"html": "A", "epub": "I", "pdf": "I"}.get(book_format))


def urlencode(url):
    return urllib.parse.quote(url)


jinja_env.filters["book_name_for_fs"] = book_name_for_fs
jinja_env.filters["zim_link_prefix"] = zim_link_prefix
jinja_env.filters["language_name"] = language_name
jinja_env.filters["fa_for_format"] = fa_for_format
jinja_env.filters["urlencode"] = urlencode
jinja_env.filters["article_name_for"] = lambda book, cover=False: article_name_for(
    book, cover=cover
)
jinja_env.filters["archive_name_for"] = archive_name_for


def generate_noscript_pages(
    formats: list[str],
    work_store: WorkStore,
    assembler: ZimAssembler,
    *,
    display_name: str,
    collection_label: str = "Collections",
    indexes: Indexes,
) -> None:
    """Generate No-JavaScript fallback HTML pages"""
    logger.info("Generating No-JS fallback pages")

    # Add common CSS file to ZIM
    common_css = (
        resources.files("gutenberg2zim") / "templates" / "noscript" / "common.css"
    )
    if common_css.is_file():
        logger.debug("Adding noscript/common.css to ZIM")
        assembler.add_item_for(
            path="noscript/common.css",
            content=common_css.read_bytes(),
            mimetype="text/css",
            is_front=False,
        )
    all_works = list(work_store.works)
    all_authors = indexes.authors
    collection_works_map: dict[str, list[Work]] = {}
    collection_names: dict[str, str] = {}
    for work in all_works:
        for collection in work.collections:
            collection_works_map.setdefault(collection.id, []).append(work)
            collection_names.setdefault(collection.id, collection.name)
    # Template-friendly views, shared across all pages
    book_contexts = {work.id: work_template_context(work) for work in all_works}
    author_contexts = {
        creator.id: creator_template_context(creator) for creator in all_authors
    }

    # Generate books listing page
    logger.debug("Generating noscript/books.html")
    books_template = jinja_env.get_template("noscript/books.html")
    books_html = books_template.render(
        books=list(book_contexts.values()),
        formats=formats,
        display_name=display_name,
    )
    assembler.add_item_for(
        path="noscript/books.html",
        content=books_html,
        mimetype="text/html",
        is_front=False,
        title=f"All Books - {display_name}",
        auto_index=False,
    )

    # Generate authors listing page
    logger.debug("Generating noscript/authors.html")
    # Reuse the shared per-author index for book counts
    works_map = indexes.by_author
    author_book_counts = {
        author_id: len(works) for author_id, works in works_map.items()
    }
    authors_template = jinja_env.get_template("noscript/authors.html")
    authors_html = authors_template.render(
        authors=list(author_contexts.values()),
        all_books=list(book_contexts.values()),
        author_book_counts=author_book_counts,
        display_name=display_name,
    )
    assembler.add_item_for(
        path="noscript/authors.html",
        content=authors_html,
        mimetype="text/html",
        is_front=False,
        title=f"All Authors - {display_name}",
        auto_index=False,
    )

    logger.debug("Generating noscript/collections.html")
    collections_template = jinja_env.get_template("noscript/collections.html")
    collections_html = collections_template.render(
        collections=[
            {
                "id": collection_id,
                "key": collection_key(collection_id),
                "name": collection_names[collection_id],
                "book_count": len(collection_works_map[collection_id]),
            }
            for collection_id in sorted(
                collection_works_map,
                key=lambda collection_id: collection_names[collection_id],
            )
        ],
        display_name=display_name,
        collection_label=collection_label,
    )
    assembler.add_item_for(
        path="noscript/collections.html",
        content=collections_html,
        mimetype="text/html",
        is_front=False,
        title=f"{collection_label} - {display_name}",
        auto_index=False,
    )

    logger.debug("Generating No-JS collection detail pages")
    collection_template = jinja_env.get_template("noscript/collection.html")
    for collection_id, collection_works in collection_works_map.items():
        collection_books = [book_contexts[work.id] for work in collection_works]
        collection_html = collection_template.render(
            collection_id=collection_id,
            collection_key=collection_key(collection_id),
            collection_name=collection_names[collection_id],
            books=collection_books,
            formats=formats,
            display_name=display_name,
            collection_label=collection_label,
        )
        assembler.add_item_for(
            path=f"noscript/collection_{collection_key(collection_id)}.html",
            content=collection_html,
            mimetype="text/html",
            is_front=False,
            title=f"{collection_label}: {collection_names[collection_id]}",
            auto_index=False,
        )

    # Generate individual book pages
    logger.debug("Generating No-JS book detail pages")
    book_template = jinja_env.get_template("noscript/book.html")
    for work in all_works:
        book_html = book_template.render(
            book=book_contexts[work.id],
            formats=formats,
            display_name=display_name,
        )
        assembler.add_item_for(
            path=f"noscript/book_{work.id}.html",
            content=book_html,
            mimetype="text/html",
            is_front=False,
            title=work.title,
            auto_index=False,
        )

    # Generate individual author pages
    logger.debug("Generating No-JS author pages")
    author_template = jinja_env.get_template("noscript/author.html")
    for creator in all_authors:
        author_books = [
            book_contexts[work.id] for work in works_map.get(creator.id, [])
        ]
        author_html = author_template.render(
            author=author_contexts[creator.id],
            author_books=author_books,
            display_name=display_name,
        )
        assembler.add_item_for(
            path=f"noscript/author_{creator.id}.html",
            content=author_html,
            mimetype="text/html",
            is_front=False,
            title=creator.name,
            auto_index=False,
        )

    logger.info("No-JS fallback pages generation completed")
