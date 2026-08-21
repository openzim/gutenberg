"""No-JavaScript fallback HTML pages exporter (moved from `gutenberg2zim.export`).

Renders the `noscript/` Jinja templates so the ZIM remains browsable when
the Vue.js UI cannot run. Owns the shared `jinja_env` and its filters.
"""

import urllib.parse
from importlib import resources

from jinja2 import Environment, PackageLoader, select_autoescape

from gutenberg2zim.constants import logger
from gutenberg2zim.core.exporters.catalog_data import collections_for_works
from gutenberg2zim.core.index_builder import Indexes
from gutenberg2zim.core.language import language_name
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.utils import (
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    creator_template_context,
    work_lcc_shelf,
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
    shelves = collections_for_works(all_works)
    shelf_works_map: dict[str, list[Work]] = {
        shelf_code: [work for work in all_works if work_lcc_shelf(work) == shelf_code]
        for shelf_code in shelves
    }
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

    logger.debug("Generating noscript/lcc_shelves.html")
    shelves_template = jinja_env.get_template("noscript/lcc_shelves.html")
    shelves_html = shelves_template.render(
        shelves=[
            {
                "code": code,
                "book_count": len(shelf_works_map.get(code, [])),
            }
            for code in shelves
        ],
        display_name=display_name,
    )
    assembler.add_item_for(
        path="noscript/lcc_shelves.html",
        content=shelves_html,
        mimetype="text/html",
        is_front=False,
        title=f"LCC Shelves - {display_name}",
        auto_index=False,
    )

    logger.debug("Generating No-JS LCC shelf detail pages")
    shelf_template = jinja_env.get_template("noscript/lcc_shelf.html")
    for shelf_code in shelves:
        shelf_books = [
            book_contexts[work.id] for work in shelf_works_map.get(shelf_code, [])
        ]
        shelf_html = shelf_template.render(
            shelf_code=shelf_code,
            books=shelf_books,
            formats=formats,
            display_name=display_name,
        )
        assembler.add_item_for(
            path=f"noscript/lcc_shelf_{shelf_code}.html",
            content=shelf_html,
            mimetype="text/html",
            is_front=False,
            title=f"LCC Shelf {shelf_code}",
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
