"""JSON files exporter for the frontend UI (moved from `gutenberg2zim.export`).

Generates books.json, authors.json, LCC shelves JSON, config.json, the
per-item detail JSON files, and the ZIM index entries pointing at the
corresponding UI routes.
"""

from collections.abc import Iterable
from html import escape

from zimscraperlib.zim.indexing import IndexData

from gutenberg2zim.constants import logger
from gutenberg2zim.core.schemas import (
    Author as AuthorSchema,
)
from gutenberg2zim.core.schemas import (
    AuthorDetail,
    AuthorPreview,
    Authors,
    BookFormat,
    BookPreview,
    Books,
    Config,
    LCCShelf,
    LCCShelfPreview,
    LCCShelves,
)
from gutenberg2zim.core.schemas import (
    Book as BookSchema,
)
from gutenberg2zim.core.utils import archive_name_for, article_name_for
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler
from gutenberg2zim.sources.gutenberg.adapters import work_to_book
from gutenberg2zim.sources.gutenberg.models import Author, Book


def _all_books(work_store: WorkStore) -> list[Book]:
    """Get all works from the store, converted back to legacy Book objects"""
    return [work_to_book(work) for work in work_store.works]


def _lcc_shelf_list_for_books(books: Iterable[Book]):
    return sorted({book.lcc_shelf for book in books if book.lcc_shelf})


def lcc_shelf_list(work_store: WorkStore):
    return _lcc_shelf_list_for_books(_all_books(work_store))


def lcc_shelf_list_language(lang, work_store: WorkStore):
    return _lcc_shelf_list_for_books(
        filter(lambda book: lang in book.languages, _all_books(work_store))
    )


def _build_author_books_map(books: Iterable[Book]) -> dict[str, list[Book]]:
    """Build a mapping from author gut_id to their books."""
    author_books_map: dict[str, list[Book]] = {}
    for book in books:
        author_id = book.author.gut_id
        if author_id not in author_books_map:
            author_books_map[author_id] = []
        author_books_map[author_id].append(book)
    return author_books_map


# JSON Generation Functions for Vue.js UI


def _get_authors_with_books(work_store: WorkStore) -> list[Author]:
    """Get only authors who have at least one book in the work store"""
    all_books = _all_books(work_store)
    authors_dict = {book.author.gut_id: book.author for book in all_books}
    return list(authors_dict.values())


def _author_to_preview(
    author: Author, author_stats: dict[str, tuple[int, int]]
) -> AuthorPreview:
    """Convert Author dataclass to AuthorPreview schema"""
    book_count, total_popularity = author_stats.get(author.gut_id, (0, 0))
    return AuthorPreview(
        id=author.gut_id,
        name=author.name(),
        book_count=book_count,
        total_popularity=total_popularity,
    )


def _author_to_schema(author: Author) -> AuthorSchema:
    """Convert Author dataclass to Author schema"""
    return AuthorSchema(
        id=author.gut_id,
        first_name=author.first_names,
        last_name=author.last_name,
        birth_year=author.birth_year,
        death_year=author.death_year,
        name=author.name(),
    )


def _cover_path_for(book: Book) -> str | None:
    return f"covers/{book.book_id}_cover_image.webp" if book.has_cover else None


def _book_to_preview(
    book: Book, formats: list[str], author_stats: dict[str, tuple[int, int]]
) -> BookPreview:
    """Convert Book dataclass to BookPreview schema"""
    cover_path = _cover_path_for(book)

    return BookPreview(
        id=book.book_id,
        title=book.title,
        author=_author_to_preview(book.author, author_stats),
        languages=book.languages,
        popularity=book.popularity,
        cover_path=cover_path,
        lcc_shelf=book.lcc_shelf,
        available_formats=book.requested_formats(formats),
        description=book.description,
    )


def _book_to_schema(book: Book, formats: list[str]) -> BookSchema:
    """Convert Book dataclass to Book schema with formats"""
    cover_path = _cover_path_for(book)

    book_formats: list[BookFormat] = []
    available_formats = book.requested_formats(formats)

    for fmt in formats:
        if fmt in available_formats:
            if fmt == "html":
                path = article_name_for(book)
            else:
                path = archive_name_for(book, fmt)
            book_formats.append(
                BookFormat(
                    format=fmt,
                    path=path,
                    available=True,
                )
            )
        else:
            book_formats.append(
                BookFormat(
                    format=fmt,
                    path="",
                    available=False,
                )
            )

    return BookSchema(
        id=book.book_id,
        title=book.title,
        subtitle=book.subtitle,
        author=_author_to_schema(book.author),
        languages=book.languages,
        license=book.license,
        downloads=book.downloads,
        popularity=book.popularity,
        lcc_shelf=book.lcc_shelf,
        cover_path=cover_path,
        formats=book_formats,
        description=book.description,
    )


def _lcc_shelf_to_preview(shelf_code: str, all_books: list[Book]) -> LCCShelfPreview:
    """Convert LCC shelf code to LCCShelfPreview schema"""
    shelf_books = [book for book in all_books if book.lcc_shelf == shelf_code]
    book_count = len(shelf_books)
    total_popularity = sum(book.popularity for book in shelf_books)
    return LCCShelfPreview(
        code=shelf_code,
        name=None,
        book_count=book_count,
        total_popularity=total_popularity,
    )


def add_index_entry(
    title: str, content: str, fname: str, vue_route: str, assembler: ZimAssembler
) -> None:
    """Add a custom item to the ZIM index with HTML redirect to Vue.js route.

    Args:
        title: Title for the index entry
        content: Content/description for search indexing
        fname: Filename for the index entry (e.g., "book_12345")
        vue_route: Vue.js route path (e.g., "book/12345")
        assembler: The ZIM assembler to add the item to
    """
    redirect_url = f"../index.html#/{vue_route}"
    safe_title = escape(title)
    safe_content = escape(content)
    safe_redirect_url = escape(redirect_url, quote=True)
    html_content = (
        f"<html><head><title>{safe_title}</title>"
        f'<meta http-equiv="refresh" content="0;URL=\'{safe_redirect_url}\'" />'
        f"</head><body>{safe_content}</body></html>"
    )

    logger.debug(f"Adding {fname} to ZIM index")
    assembler.add_item_for(
        title=title,
        path=f"index/{fname}",
        content=html_content,
        mimetype="text/html",
        index_data=IndexData(title=title, content=content),
    )


def generate_json_files(
    zim_name: str,
    formats: list[str],
    work_store: WorkStore,
    assembler: ZimAssembler,
    title: str | None = None,
    description: str | None = None,
    *,
    add_lcc_shelves: bool = False,
    primary_color: str | None = None,
    secondary_color: str | None = None,
) -> None:
    """Generate all JSON files for Vue.js frontend"""
    logger.info("Generating JSON files for Vue.js UI")

    # Maximum number of books to include in index entries
    max_books_in_index = 10

    # Fetch data once and reuse
    all_books = _all_books(work_store)
    all_authors = _get_authors_with_books(work_store)

    # Build author stats once for O(1) lookups
    author_stats: dict[str, tuple[int, int]] = {}
    for book in all_books:
        gut_id = book.author.gut_id
        count, pop = author_stats.get(gut_id, (0, 0))
        author_stats[gut_id] = (count + 1, pop + book.popularity)

    logger.info("Generating high-level JSON files")
    logger.debug("Generating books.json")
    books_preview = [
        _book_to_preview(book, formats, author_stats) for book in all_books
    ]
    books_collection = Books(books=books_preview, total_count=len(books_preview))
    assembler.add_item_for(
        path="books.json",
        content=books_collection.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    logger.debug("Generating authors.json")
    authors_preview = [
        _author_to_preview(author, author_stats) for author in all_authors
    ]
    authors_collection = Authors(
        authors=authors_preview, total_count=len(authors_preview)
    )
    assembler.add_item_for(
        path="authors.json",
        content=authors_collection.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    if add_lcc_shelves:
        logger.debug("Generating lcc_shelves.json")
        shelves = _lcc_shelf_list_for_books(all_books)
        shelves_preview = [
            _lcc_shelf_to_preview(shelf_code, all_books) for shelf_code in shelves
        ]
        shelves_collection = LCCShelves(
            shelves=shelves_preview, total_count=len(shelves_preview)
        )
        assembler.add_item_for(
            path="lcc_shelves.json",
            content=shelves_collection.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

    logger.debug("Generating config.json")
    config = Config(
        title=title or zim_name or "Project Gutenberg Library",
        description=description,
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
    assembler.add_item_for(
        path="config.json",
        content=config.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    logger.info("Generating detail JSON files")
    logger.debug("Generating book detail files and index entries")
    for book in all_books:
        book_detail = _book_to_schema(book, formats)
        assembler.add_item_for(
            path=f"books/{book.book_id}.json",
            content=book_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

        # Add index entry for book
        book_description = book_detail.description or f"Book by {book.author.name()}"
        # Build searchable content with key metadata
        index_parts = [book_description, f"by {book.author.name()}"]

        if book.subtitle:
            index_parts.insert(0, book.subtitle)
        if book.languages:
            index_parts.append(f"Languages: {', '.join(book.languages)}")
        if book.lcc_shelf:
            index_parts.append(f"LCC Shelf: {book.lcc_shelf}")

        add_index_entry(
            title=book.title,
            content=". ".join(index_parts) + ".",
            fname=f"book_{book.book_id}",
            vue_route=f"book/{book.book_id}",
            assembler=assembler,
        )

    logger.debug("Generating author detail files and index entries")
    # Build author_id -> books mapping once to avoid O(authors * books) scans
    author_books_map = _build_author_books_map(all_books)

    for author in all_authors:
        author_books = [
            _book_to_preview(book, formats, author_stats)
            for book in author_books_map.get(author.gut_id, [])
        ]
        author_detail = AuthorDetail(
            id=author.gut_id,
            first_name=author.first_names,
            last_name=author.last_name,
            birth_year=author.birth_year,
            death_year=author.death_year,
            name=author.name(),
            books=author_books,
            book_count=len(author_books),
        )

        assembler.add_item_for(
            path=f"authors/{author.gut_id}.json",
            content=author_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

        # Add index entry for author
        author_parts = [f"Author: {author.name()}"]

        if author.birth_year or author.death_year:
            years = f"{author.birth_year or ''} - {author.death_year or ''}".strip(" -")
            author_parts.append(f"({years})")

        author_parts.append(f"{len(author_books)} book(s)")

        # Add book titles for searchability
        if author_books:
            titles = [book.title for book in author_books[:max_books_in_index]]
            author_parts.append("Books: " + ", ".join(titles))
            if len(author_books) > max_books_in_index:
                author_parts.append(
                    f"and {len(author_books) - max_books_in_index} more"
                )

        add_index_entry(
            title=author.name(),
            content=". ".join(author_parts) + ".",
            fname=f"author_{author.gut_id}",
            vue_route=f"author/{author.gut_id}",
            assembler=assembler,
        )

    if add_lcc_shelves:
        logger.debug("Generating LCC shelf detail files and index entries")
        for shelf_code in shelves:
            shelf_books = [
                _book_to_preview(book, formats, author_stats)
                for book in all_books
                if book.lcc_shelf == shelf_code
            ]
            shelf_detail = LCCShelf(
                code=shelf_code,
                name=None,
                books=shelf_books,
                book_count=len(shelf_books),
            )
            assembler.add_item_for(
                path=f"lcc_shelves/{shelf_code}.json",
                content=shelf_detail.model_dump_json(by_alias=True, indent=2),
                mimetype="application/json",
                is_front=False,
            )

            shelf_title = f"LCC Shelf {shelf_code}"
            shelf_parts = [
                f"Library of Congress Classification shelf {shelf_code}",
                f"{len(shelf_books)} book(s)",
            ]

            # Add book titles and authors for searchability
            if shelf_books:
                book_entries = [
                    f"{book.title} by {book.author.name}"
                    for book in shelf_books[:max_books_in_index]
                ]
                shelf_parts.append("Books: " + ", ".join(book_entries))
                if len(shelf_books) > max_books_in_index:
                    shelf_parts.append(
                        f"and {len(shelf_books) - max_books_in_index} more"
                    )

            add_index_entry(
                title=shelf_title,
                content=". ".join(shelf_parts) + ".",
                fname=f"lcc_shelf_{shelf_code}",
                vue_route=f"lcc-shelf/{shelf_code}",
                assembler=assembler,
            )

    # Add index entries for main listing pages
    add_index_entry(
        title="All Books - Project Gutenberg",
        content=f"Browse all {len(all_books)} books available in Project Gutenberg. "
        f"Search and filter by language, format, author, and more.",
        fname="books_list",
        vue_route="books",
        assembler=assembler,
    )

    add_index_entry(
        title="All Authors - Project Gutenberg",
        content=f"Browse all {len(all_authors)} authors in Project Gutenberg. "
        f"Discover books by your favorite authors.",
        fname="authors_list",
        vue_route="authors",
        assembler=assembler,
    )

    if add_lcc_shelves:
        add_index_entry(
            title="LCC Shelves - Project Gutenberg",
            content=f"Browse books by Library of Congress Classification. "
            f"{len(shelves)} shelves available covering various subjects and topics.",
            fname="lcc_shelves_list",
            vue_route="lcc-shelves",
            assembler=assembler,
        )

    logger.info("JSON file generation completed")
