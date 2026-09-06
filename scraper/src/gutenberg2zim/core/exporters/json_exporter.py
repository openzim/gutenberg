"""JSON files exporter for the frontend UI (moved from `gutenberg2zim.export`).

Generates books.json, authors.json, collections JSON, config.json, and the
per-item detail JSON files. The ZIM search index entries pointing at the
UI routes live in `search_items_exporter`.
"""

from collections import defaultdict

from gutenberg2zim.constants import logger
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
    Collection,
    CollectionPreview,
    Collections,
    Config,
    FeatureFlags,
    SourceInfo,
    ThemeConfig,
)
from gutenberg2zim.core.schemas import (
    Book as BookSchema,
)
from gutenberg2zim.core.utils import (
    archive_name_for,
    article_name_for,
    collection_key,
    creator_birth_year,
    creator_death_year,
    primary_collection_id,
    primary_creator,
    requested_formats,
)
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler

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
        primary_collection=primary_collection_id(work),
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
        primary_metric=work.primary_metric or 0,
        popularity=work.popularity or 0,
        primary_collection=primary_collection_id(work),
        cover_path=_cover_path_for(work),
        formats=book_formats,
        description=work.description,
    )


def _collection_to_preview(
    collection_id: str, collection_name: str, collection_works: list[Work]
) -> CollectionPreview:
    return CollectionPreview(
        id=collection_id,
        name=collection_name,
        book_count=len(collection_works),
        total_popularity=sum(work.popularity or 0 for work in collection_works),
    )


def generate_json_files(
    zim_name: str,
    formats: list[str],
    work_store: WorkStore,
    assembler: ZimAssembler,
    title: str | None = None,
    description: str | None = None,
    *,
    primary_color: str | None = None,
    secondary_color: str | None = None,
    display_name: str,
    indexes: Indexes,
    source_slug: str = "source",
    source_description: str | None = None,
    collection_label: str = "Collections",
    collection_icon_style: str = "classification",
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

    collection_works_map: dict[str, list[Work]] = defaultdict(list)
    collection_names: dict[str, str] = {}
    for work in all_works:
        for collection in work.collections:
            collection_works_map[collection.id].append(work)
            collection_names.setdefault(collection.id, collection.name)
    collection_ids = sorted(
        collection_works_map,
        key=lambda collection_id: collection_names[collection_id],
    )

    collections = Collections(
        collections=[
            _collection_to_preview(
                collection_id,
                collection_names[collection_id],
                collection_works_map[collection_id],
            )
            for collection_id in collection_ids
        ],
        total_count=len(collection_ids),
    )
    assembler.add_item_for(
        path="collections.json",
        content=collections.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )
    assembler.add_item_for(
        path="authors.json",
        content=authors_collection.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    logger.debug("Generating config.json")
    config = Config(
        title=title or zim_name or f"{display_name} Library",
        description=description,
        primary_color=primary_color,
        secondary_color=secondary_color,
        source=SourceInfo(
            slug=source_slug,
            name=display_name,
            description=source_description or display_name,
        ),
        theme=ThemeConfig(
            primary_color=primary_color,
            secondary_color=secondary_color,
            format_icons={format_name: format_name for format_name in formats},
            route_labels={
                "home": "Home",
                "works": "eBooks",
                "authors": "Authors",
                "collections": collection_label,
            },
            collection_icon_style=collection_icon_style,
        ),
        features=FeatureFlags(
            epub_reader="epub" in formats,
            pdf_reader="pdf" in formats,
            noscript_fallback=True,
        ),
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

    for collection_id in collection_ids:
        collection_works = collection_works_map[collection_id]
        collection = Collection(
            id=collection_id,
            name=collection_names[collection_id],
            book_count=len(collection_works),
            total_popularity=sum(work.popularity or 0 for work in collection_works),
            books=[
                _work_to_preview(work, formats, author_stats)
                for work in collection_works
            ],
        )
        assembler.add_item_for(
            path=f"collections/{collection_key(collection_id)}.json",
            content=collection.model_dump_json(by_alias=True, indent=2),
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

    logger.info("JSON file generation completed")
