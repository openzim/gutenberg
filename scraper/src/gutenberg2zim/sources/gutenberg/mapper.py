"""Gutenberg collection mapping.

Maps a work to the collections it belongs to. Gutenberg's only structured
classification is the LoCC (Library of Congress Classification), which the
RDF/CSV metadata provides as a raw code (e.g. "PR", "QA", "b123") and which
we normalize to a shelf identifier via `transform_locc_code`.
"""

from gutenberg2zim.core.models import CollectionRef, Work
from gutenberg2zim.core.ports import CollectionMapperPort
from gutenberg2zim.sources.gutenberg.catalog import (
    LCC_SHELF_KIND,
    transform_locc_code,
)


class GutenbergCollectionMapper(CollectionMapperPort):
    """`CollectionMapperPort` implementation for LoCC shelves"""

    def map(self, work: Work) -> list[CollectionRef]:
        # Collections already mapped by other means pass through untouched
        collections = [c for c in work.collections if c.kind != LCC_SHELF_KIND]

        # Prefer the shelf already present on the work; else derive it from a
        # raw LoCC code carried in extra (e.g. straight from the catalog/RDF)
        shelf = next((c.id for c in work.collections if c.kind == LCC_SHELF_KIND), None)
        if shelf is None:
            raw_locc = work.extra.get("locc") or work.extra.get("lcc_shelf")
            if raw_locc:
                shelf = transform_locc_code(str(raw_locc))

        if shelf:
            collections.append(CollectionRef(id=shelf, name=shelf, kind=LCC_SHELF_KIND))
        return collections
