"""JSON files exporter for the frontend UI (moved from `gutenberg2zim.export`).

Generates books.json, authors.json, LCC shelves JSON, config.json, and the
per-item detail JSON files. The ZIM search index entries pointing at the
UI routes live in `search_items_exporter`.
"""

from collections import defaultdict

from gutenberg2zim.constants import logger
from gutenberg2zim.core.exporters.catalog_data import collections_for_works
from gutenberg2zim.core.index_builder import Indexes
from gutenberg2zim.core.models import Creator, Work
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
from gutenberg2zim.core.utils import (
    archive_name_for,
    article_name_for,
    creator_birth_year,
    creator_death_year,
    primary_creator,
    requested_formats,
    work_lcc_shelf,
)
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler


def lcc_shelf_list(work_store: WorkStore):
    return collections_for_works(work_store.works)


def lcc_shelf_list_language(lang, work_store: WorkStore):
    return collections_for_works(
        work for work in work_store.works if lang in work.languages
    )


# JSON Generation Functions for Vue.js UI


def _creator_to_preview(
    creator: Creator, author_stats: dict[str, tuple[int, int]]
) -> AuthorPreview:
    """Convert Creator to AuthorPreview schema"""
    book_count, total_popularity = author_stats.get(creator.id, (0, 0))
    return AuthorPreview(
        id=creator.id,
        name=creator.name,
        book_count=book_count,
        total_popularity=total_popularity,
    )


def _creator_to_schema(creator: Creator) -> AuthorSchema:
    """Convert Creator to Author schema"""
    return AuthorSchema(
        id=creator.id,
        first_name=creator.extra.get("first_names"),
        last_name=creator.sort_name or "",
        birth_year=creator_birth_year(creator),
        death_year=creator_death_year(creator),
        name=creator.name,
    )


def _cover_path_for(work: Work) -> str | None:
    has_cover = work.extra.get("has_cover", work.cover is not None)
    return f"covers/{work.id}_cover_image.webp" if has_cover else None


def _work_to_preview(
    work: Work, formats: list[str], author_stats: dict[str, tuple[int, int]]
) -> BookPreview:
    """Convert Work to BookPreview schema"""
    return BookPreview(
        id=work.id,
        title=work.title,
        author=_creator_to_preview(primary_creator(work), author_stats),
        languages=work.languages,
        popularity=work.popularity or 0,
        cover_path=_cover_path_for(work),
        lcc_shelf=work_lcc_shelf(work),
        available_formats=requested_formats(work, formats),
        description=work.description,
    )


def _work_to_schema(work: Work, formats: list[str]) -> BookSchema:
    """Convert Work to Book schema with formats"""
    book_formats: list[BookFormat] = []
    available_formats = requested_formats(work, formats)

    for fmt in formats:
        if fmt in available_formats:
            if fmt == "html":
                path = article_name_for(work)
            else:
                path = archive_name_for(work, fmt)
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
        id=work.id,
        title=work.title,
        subtitle=work.subtitle,
        author=_creator_to_schema(primary_creator(work)),
        languages=work.languages,
        license=work.license or "Public domain in the USA.",
        downloads=work.extra.get("downloads", 0),
        popularity=work.popularity or 0,
        lcc_shelf=work_lcc_shelf(work),
        cover_path=_cover_path_for(work),
        formats=book_formats,
        description=work.description,
    )


def _lcc_shelf_to_preview(shelf_code: str, shelf_works: list[Work]) -> LCCShelfPreview:
    """Convert LCC shelf code to LCCShelfPreview schema"""
    book_count = len(shelf_works)
    total_popularity = sum(work.popularity or 0 for work in shelf_works)
    return LCCShelfPreview(
        code=shelf_code,
        name=None,
        book_count=book_count,
        total_popularity=total_popularity,
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
    display_name: str,
    indexes: Indexes,
) -> None:
    """Generate all JSON files for Vue.js frontend"""
    logger.info("Generating JSON files for Vue.js UI")

    # Fetch data once and reuse
    all_works = list(work_store.works)
    all_creators = indexes.authors
    author_stats = indexes.author_stats

    logger.info("Generating high-level JSON files")
    logger.debug("Generating books.json")
    books_preview = [
        _work_to_preview(work, formats, author_stats) for work in all_works
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
        _creator_to_preview(creator, author_stats) for creator in all_creators
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

    # Group works by shelf in a single pass, shared by the shelf previews
    # and the shelf detail files
    shelf_works_map: dict[str, list[Work]] = defaultdict(list)
    if add_lcc_shelves:
        for work in all_works:
            if (shelf := work_lcc_shelf(work)) is not None:
                shelf_works_map[shelf].append(work)
    shelves = sorted(shelf_works_map)

    if add_lcc_shelves:
        logger.debug("Generating lcc_shelves.json")
        shelves_preview = [
            _lcc_shelf_to_preview(shelf_code, shelf_works_map[shelf_code])
            for shelf_code in shelves
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
        title=title or zim_name or f"{display_name} Library",
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
    logger.debug("Generating book detail files")
    for work in all_works:
        book_detail = _work_to_schema(work, formats)
        assembler.add_item_for(
            path=f"books/{work.id}.json",
            content=book_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

    logger.debug("Generating author detail files")
    for creator in all_creators:
        creator_works = [
            _work_to_preview(work, formats, author_stats)
            for work in indexes.by_author.get(creator.id, [])
        ]
        author_detail = AuthorDetail(
            id=creator.id,
            first_name=creator.extra.get("first_names"),
            last_name=creator.sort_name or "",
            birth_year=creator_birth_year(creator),
            death_year=creator_death_year(creator),
            name=creator.name,
            books=creator_works,
            book_count=len(creator_works),
        )

        assembler.add_item_for(
            path=f"authors/{creator.id}.json",
            content=author_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

    if add_lcc_shelves:
        logger.debug("Generating LCC shelf detail files")
        for shelf_code in shelves:
            shelf_works = [
                _work_to_preview(work, formats, author_stats)
                for work in shelf_works_map[shelf_code]
            ]
            shelf_detail = LCCShelf(
                code=shelf_code,
                name=None,
                books=shelf_works,
                book_count=len(shelf_works),
            )
            assembler.add_item_for(
                path=f"lcc_shelves/{shelf_code}.json",
                content=shelf_detail.model_dump_json(by_alias=True, indent=2),
                mimetype="application/json",
                is_front=False,
            )

    logger.info("JSON file generation completed")
