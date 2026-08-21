"""Shared work-store queries used by both the JSON and No-JS exporters"""

from collections.abc import Iterable

from gutenberg2zim.core.models import Work
from gutenberg2zim.core.utils import work_lcc_shelf


def collections_for_works(works: Iterable[Work]) -> list[str]:
    """Sorted shelf codes across the given works"""
    return sorted(
        {shelf for work in works if (shelf := work_lcc_shelf(work)) is not None}
    )
