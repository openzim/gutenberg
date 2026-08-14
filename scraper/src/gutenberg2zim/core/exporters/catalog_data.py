"""Shared work-store queries used by both the JSON and No-JS exporters"""

from collections.abc import Iterable

from gutenberg2zim.core.models import Work
from gutenberg2zim.core.utils import primary_collection_id


def collections_for_works(works: Iterable[Work]) -> list[str]:
    """Sorted primary collection ids across the given works."""
    return sorted(
        {
            collection
            for work in works
            if (collection := primary_collection_id(work)) is not None
        }
    )
