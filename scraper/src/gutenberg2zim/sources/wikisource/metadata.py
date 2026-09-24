"""Wikisource metadata access.

The OPDS feed entries parsed by `sources.wikisource.catalog` already carry every
field the pipeline needs, including the per-format ws-export download links, so
this port only maps a `WorkRef` into a `Work` - there is no per-book fetch.
"""

import hashlib
from collections.abc import Iterable, Iterator

from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.models import Creator, Format, Work
from gutenberg2zim.core.ports import MetadataPort, WorkRef
from gutenberg2zim.sources.wikisource.catalog import (
    BASE_URL,
    WIKISOURCE_SOURCE,
    slugify,
)


def author_id(name: str) -> str:
    """Deterministic, path-safe id shared by every work of the same author."""
    slug = slugify(name)
    digest = hashlib.sha256(name.encode()).hexdigest()[:8]
    return f"{slug}-{digest}" if slug else digest


class WikisourceMetadata(MetadataPort):
    """Maps discovered `WorkRef`s into `Work`s using the parsed feed data."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        *,
        engine: DownloadEngine,
    ):
        self._base_url = base_url.rstrip("/")
        self._engine = engine

    def fetch(self, refs: Iterable[WorkRef]) -> Iterator[Work]:
        for ref in refs:
            yield self._to_work(ref)

    @staticmethod
    def _to_work(ref: WorkRef) -> Work:
        extra = ref.extra
        author = extra.get("author")
        creators = (
            [Creator(id=author_id(author), name=author, sort_name=author)]
            if author
            else []
        )
        language = extra.get("language")
        return Work(
            id=ref.id,
            source=WIKISOURCE_SOURCE,
            title=extra.get("title") or "Untitled",
            creators=creators,
            languages=[language] if language else [],
            license=extra.get("license"),
            formats=[
                Format(name=name, media_type=media_type, url=url)
                for name, media_type, url in extra.get("formats", [])
            ],
            source_url=extra.get("source_url"),
            extra={
                "issued": extra.get("issued"),
                "wikisource_page": extra.get("page"),
            },
        )
