"""Build derived indexes from the work store in a single pass.

The exporters need the same derivations over and over (works grouped by
creator, works grouped by collection, per-creator stats, search index
entries). Building them once here keeps that work O(n) over the catalog
and keeps the derivations source-agnostic: everything is computed from
`core.models.Work`, never from source-specific records.

The search entries reproduce exactly the on-ZIM index format historically
emitted by `core.exporters.json_exporter` (fnames, routes and payload
strings, max `MAX_WORKS_IN_ENTRY` works listed per entry), so the existing
UI keeps working.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from gutenberg2zim.core.models import Creator, Work
from gutenberg2zim.core.utils import (
    creator_birth_year,
    creator_death_year,
    primary_creator,
    work_creators,
    work_lcc_shelf,
)
from gutenberg2zim.core.work_store import WorkStore

# Maximum number of works to list inside one search entry's content
MAX_WORKS_IN_ENTRY = 10


@dataclass(frozen=True, slots=True)
class IndexEntry:
    """One entry for the ZIM search index, pointing at a UI route"""

    title: str
    content: str
    fname: str
    route: str


@dataclass(slots=True)
class Indexes:
    """Everything the exporters need, derived once from the work store"""

    # creators having at least one work, deduplicated by id, in work order
    authors: list[Creator] = field(default_factory=list)
    by_author: dict[str, list[Work]] = field(default_factory=dict)
    by_collection: dict[str, list[Work]] = field(default_factory=dict)
    # creator id -> (work count, summed popularity; works without a
    # popularity value count for the work count only)
    author_stats: dict[str, tuple[int, int]] = field(default_factory=dict)
    search_entries: list[IndexEntry] = field(default_factory=list)


class IndexBuilder:
    def __init__(self, store: WorkStore):
        self._store = store

    def build(self, *, add_lcc_shelves: bool = False, display_name: str) -> Indexes:
        authors: dict[str, Creator] = {}
        by_author: dict[str, list[Work]] = defaultdict(list)
        by_collection: dict[str, list[Work]] = defaultdict(list)
        # shelf grouping (a work's primary collection) for the search entries
        by_shelf: dict[str, list[Work]] = defaultdict(list)
        author_stats: dict[str, tuple[int, int]] = {}

        works = self._store.works
        for work in works:
            for creator in work_creators(work):
                authors.setdefault(creator.id, creator)
                by_author[creator.id].append(work)
                count, popularity = author_stats.get(creator.id, (0, 0))
                author_stats[creator.id] = (
                    count + 1,
                    popularity + (work.popularity or 0),
                )
            for collection in work.collections:
                by_collection[collection.id].append(work)
            if shelf := work_lcc_shelf(work):
                by_shelf[shelf].append(work)

        search_entries = list(
            self._search_entries(
                works,
                list(authors.values()),
                by_author,
                by_shelf,
                add_lcc_shelves=add_lcc_shelves,
                display_name=display_name,
            )
        )

        return Indexes(
            authors=list(authors.values()),
            by_author=dict(by_author),
            by_collection=dict(by_collection),
            author_stats=author_stats,
            search_entries=search_entries,
        )

    def _search_entries(
        self,
        works: list[Work],
        authors: list[Creator],
        by_author: dict[str, list[Work]],
        by_shelf: dict[str, list[Work]],
        *,
        add_lcc_shelves: bool,
        display_name: str,
    ) -> Iterable[IndexEntry]:
        for work in works:
            creator = primary_creator(work)
            parts = [
                work.description or f"Book by {creator.name}",
                f"by {creator.name}",
            ]
            if work.subtitle:
                parts.insert(0, work.subtitle)
            if work.languages:
                parts.append(f"Languages: {', '.join(work.languages)}")
            lcc_shelf = work_lcc_shelf(work)
            if lcc_shelf:
                parts.append(f"LCC Shelf: {lcc_shelf}")
            yield IndexEntry(
                title=work.title,
                content=". ".join(parts) + ".",
                fname=f"book_{work.id}",
                route=f"book/{work.id}",
            )

        for creator in authors:
            creator_works = by_author.get(creator.id, [])
            parts = [f"Author: {creator.name}"]
            birth_year = creator_birth_year(creator)
            death_year = creator_death_year(creator)
            if birth_year or death_year:
                years = f"{birth_year or ''} - {death_year or ''}".strip(" -")
                parts.append(f"({years})")
            parts.append(f"{len(creator_works)} book(s)")
            if creator_works:
                titles = [work.title for work in creator_works[:MAX_WORKS_IN_ENTRY]]
                parts.append("Books: " + ", ".join(titles))
                if len(creator_works) > MAX_WORKS_IN_ENTRY:
                    parts.append(f"and {len(creator_works) - MAX_WORKS_IN_ENTRY} more")
            yield IndexEntry(
                title=creator.name,
                content=". ".join(parts) + ".",
                fname=f"author_{creator.id}",
                route=f"author/{creator.id}",
            )

        if add_lcc_shelves:
            for shelf_code in sorted(by_shelf):
                shelf_works = by_shelf[shelf_code]
                parts = [
                    f"Library of Congress Classification shelf {shelf_code}",
                    f"{len(shelf_works)} book(s)",
                ]
                if shelf_works:
                    entries = [
                        f"{work.title} by {primary_creator(work).name}"
                        for work in shelf_works[:MAX_WORKS_IN_ENTRY]
                    ]
                    parts.append("Books: " + ", ".join(entries))
                    if len(shelf_works) > MAX_WORKS_IN_ENTRY:
                        parts.append(
                            f"and {len(shelf_works) - MAX_WORKS_IN_ENTRY} more"
                        )
                yield IndexEntry(
                    title=f"LCC Shelf {shelf_code}",
                    content=". ".join(parts) + ".",
                    fname=f"lcc_shelf_{shelf_code}",
                    route=f"lcc-shelf/{shelf_code}",
                )

        # Entries for the main listing pages
        yield IndexEntry(
            title=f"All Books - {display_name}",
            content=f"Browse all {len(works)} books available in {display_name}. "
            f"Search and filter by language, format, author, and more.",
            fname="books_list",
            route="books",
        )
        yield IndexEntry(
            title=f"All Authors - {display_name}",
            content=f"Browse all {len(authors)} authors in {display_name}. "
            f"Discover books by your favorite authors.",
            fname="authors_list",
            route="authors",
        )
        if add_lcc_shelves:
            yield IndexEntry(
                title=f"LCC Shelves - {display_name}",
                content=f"Browse books by Library of Congress Classification. "
                f"{len(by_shelf)} shelves available covering various subjects and "
                f"topics.",
                fname="lcc_shelves_list",
                route="lcc-shelves",
            )
