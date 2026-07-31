"""Conversions between the Gutenberg models and the core domain model.

These adapters allow gradual migration: existing code keeps producing
`Book`/`Author` while new code consumes `Work`/`Creator`. They are
deliberately lossless for the Gutenberg source, so `work_to_book(book_to_work(b))`
round-trips.

This module is transitional and will be removed once nothing imports
`Book`/`Author` anymore (i.e. they are fully replaced by `Work`/`Creator`).

It lives in the Gutenberg source package (not in `core/`) because it is
Gutenberg-specific; `core/` must stay source-agnostic.
"""

from gutenberg2zim.core.models import CollectionRef, Cover, Creator, Work
from gutenberg2zim.sources.gutenberg.models import Author, Book

GUTENBERG_SOURCE = "gutenberg"
LCC_SHELF_KIND = "lcc_shelf"


def _parse_year(value: str | None) -> int | None:
    """Parse a year from legacy string fields, None if missing or not numeric"""
    if value and value.strip().isdigit():
        return int(value.strip())
    return None


def author_to_creator(author: Author) -> Creator:
    return Creator(
        id=author.gut_id,
        name=author.name(),
        sort_name=author.last_name or None,
        birth_date=_parse_year(author.birth_year),
        death_date=_parse_year(author.death_year),
        extra={
            "first_names": author.first_names,
            "birth_year_raw": author.birth_year,
            "death_year_raw": author.death_year,
        },
    )


def creator_to_author(creator: Creator) -> Author:
    # Recover the original split fields if this Creator came from author_to_creator
    if "first_names" in creator.extra or "birth_year_raw" in creator.extra:
        return Author(
            gut_id=creator.id,
            last_name=creator.sort_name or "",
            first_names=creator.extra.get("first_names"),
            birth_year=creator.extra.get("birth_year_raw"),
            death_year=creator.extra.get("death_year_raw"),
        )
    # Best effort for Creators built by other means: last word as last name
    parts = creator.name.rsplit(" ", 1)
    return Author(
        gut_id=creator.id,
        last_name=parts[-1],
        first_names=parts[0] if len(parts) > 1 else None,
        birth_year=str(creator.birth_date) if creator.birth_date is not None else None,
        death_year=str(creator.death_date) if creator.death_date is not None else None,
    )


def book_to_work(book: Book) -> Work:
    collections = []
    if book.lcc_shelf:
        collections.append(
            CollectionRef(id=book.lcc_shelf, name=book.lcc_shelf, kind=LCC_SHELF_KIND)
        )
    cover = None
    if book.has_cover:
        cover = Cover(
            source_url=book._cover_href,
            local_path=book.html_cover_path,
        )
    return Work(
        id=str(book.book_id),
        source=GUTENBERG_SOURCE,
        title=book.title,
        subtitle=book.subtitle,
        creators=[author_to_creator(book.author)],
        languages=list(book.languages),
        license=book.license,
        cover=cover,
        collections=collections,
        popularity=book.popularity,
        description=book.description,
        extra={
            "downloads": book.downloads,
            "unsupported_formats": list(book.unsupported_formats),
            "has_cover": book.has_cover,
        },
    )


def work_to_book(work: Work) -> Book:
    author = (
        creator_to_author(work.creators[0])
        if work.creators
        else Author("216", "Anonymous")
    )
    lcc_shelf = next((c.id for c in work.collections if c.kind == LCC_SHELF_KIND), None)
    return Book(
        book_id=int(work.id),
        title=work.title,
        subtitle=work.subtitle,
        author=author,
        languages=list(work.languages),
        license=work.license or "Public domain in the USA.",
        downloads=work.extra.get("downloads", 0),
        lcc_shelf=lcc_shelf,
        has_cover=work.extra.get("has_cover", work.cover is not None),
        description=work.description,
        unsupported_formats=list(work.extra.get("unsupported_formats", [])),
        popularity=work.popularity or 0,
        html_cover_path=work.cover.local_path if work.cover else None,
        _cover_href=work.cover.source_url if work.cover else None,
    )
