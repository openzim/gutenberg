"""No-JavaScript fallback HTML pages exporter (moved from `gutenberg2zim.export`).

Renders the `noscript/` Jinja templates so the ZIM remains browsable when
the Vue.js UI cannot run. Owns the shared `jinja_env` and its filters.
"""

import urllib.parse
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from gutenberg2zim.constants import logger
from gutenberg2zim.core.exporters.json_exporter import (
    _all_books,
    _build_author_books_map,
    _get_authors_with_books,
    _lcc_shelf_list_for_books,
)
from gutenberg2zim.core.language import language_name
from gutenberg2zim.core.utils import (
    archive_name_for,
    article_name_for,
    book_name_for_fs,
)
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler
from gutenberg2zim.sources.gutenberg.models import Book

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
) -> None:
    """Generate No-JavaScript fallback HTML pages"""
    logger.info("Generating No-JS fallback pages")

    # Add common CSS file to ZIM
    common_css_path = (
        Path(__file__).parent.parent.parent / "templates" / "noscript" / "common.css"
    )
    if common_css_path.exists():
        logger.debug("Adding noscript/common.css to ZIM")
        assembler.add_item_for(
            path="noscript/common.css",
            fpath=common_css_path,
            mimetype="text/css",
            is_front=False,
        )
    all_books = _all_books(work_store)
    all_authors = _get_authors_with_books(work_store)
    shelves = _lcc_shelf_list_for_books(all_books)
    shelf_books_map: dict[str, list[Book]] = {
        shelf_code: [book for book in all_books if book.lcc_shelf == shelf_code]
        for shelf_code in shelves
    }

    # Generate books listing page
    logger.debug("Generating noscript/books.html")
    books_template = jinja_env.get_template("noscript/books.html")
    books_html = books_template.render(
        books=all_books,
        formats=formats,
    )
    assembler.add_item_for(
        path="noscript/books.html",
        content=books_html,
        mimetype="text/html",
        is_front=False,
        title="All Books - Project Gutenberg",
        auto_index=False,
    )

    # Generate authors listing page
    logger.debug("Generating noscript/authors.html")
    # Reuse author_books_map for book counts
    author_books_map = _build_author_books_map(all_books)
    author_book_counts = {
        author_id: len(books) for author_id, books in author_books_map.items()
    }
    authors_template = jinja_env.get_template("noscript/authors.html")
    authors_html = authors_template.render(
        authors=all_authors,
        all_books=all_books,
        author_book_counts=author_book_counts,
    )
    assembler.add_item_for(
        path="noscript/authors.html",
        content=authors_html,
        mimetype="text/html",
        is_front=False,
        title="All Authors - Project Gutenberg",
        auto_index=False,
    )

    logger.debug("Generating noscript/lcc_shelves.html")
    shelves_template = jinja_env.get_template("noscript/lcc_shelves.html")
    shelves_html = shelves_template.render(
        shelves=[
            {
                "code": code,
                "book_count": len(shelf_books_map.get(code, [])),
            }
            for code in shelves
        ]
    )
    assembler.add_item_for(
        path="noscript/lcc_shelves.html",
        content=shelves_html,
        mimetype="text/html",
        is_front=False,
        title="LCC Shelves - Project Gutenberg",
        auto_index=False,
    )

    logger.debug("Generating No-JS LCC shelf detail pages")
    shelf_template = jinja_env.get_template("noscript/lcc_shelf.html")
    for shelf_code in shelves:
        shelf_books = shelf_books_map.get(shelf_code, [])
        shelf_html = shelf_template.render(
            shelf_code=shelf_code,
            books=shelf_books,
            formats=formats,
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
    for book in all_books:
        book_html = book_template.render(
            book=book,
            formats=formats,
        )
        assembler.add_item_for(
            path=f"noscript/book_{book.book_id}.html",
            content=book_html,
            mimetype="text/html",
            is_front=False,
            title=book.title,
            auto_index=False,
        )

    # Generate individual author pages
    logger.debug("Generating No-JS author pages")
    author_template = jinja_env.get_template("noscript/author.html")
    for author in all_authors:
        author_books = author_books_map.get(author.gut_id, [])
        author_html = author_template.render(
            author=author,
            author_books=author_books,
        )
        assembler.add_item_for(
            path=f"noscript/author_{author.gut_id}.html",
            content=author_html,
            mimetype="text/html",
            is_front=False,
            title=author.name(),
            auto_index=False,
        )

    logger.info("No-JS fallback pages generation completed")
