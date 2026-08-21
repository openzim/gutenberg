"""Ports (interfaces) between the source-agnostic core and a source.

Each source (Gutenberg, Standard Ebooks, ...) implements these interfaces;
the pipeline only ever talks to the abstractions. This is what keeps
`core/` free of source-specific knowledge.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from bs4 import BeautifulSoup

from gutenberg2zim.core.models import CollectionRef, Work

if TYPE_CHECKING:
    from gutenberg2zim.core.download_engine import DownloadEngine


class CatalogEntryLike(Protocol):
    """The attributes the source-agnostic layers read from a catalog entry"""

    book_id: int
    languages: list[str]
    lcc_shelf: str


class CatalogModule(Protocol):
    """Contract a source's catalog module must satisfy.

    Discovery is source-specific, so the catalog is a module rather than a
    class; profiles reference the module object directly, so a source
    missing one of these functions fails type checking at registration
    instead of at runtime.
    """

    def get_csv_fpath(self) -> Path: ...

    def download_csv_file(
        self, csv_path: Path, csv_url: str, engine: DownloadEngine
    ) -> None: ...

    def load_catalog(self, csv_path: Path) -> list[CatalogEntryLike]: ...

    def filter_books(
        self,
        catalog: list[CatalogEntryLike],
        languages: list[str] | None = None,
        only_books: list[int] | None = None,
        lcc_shelves: list[str] | None = None,
    ) -> list[CatalogEntryLike]: ...


@dataclass(frozen=True, slots=True)
class CatalogFilters:
    """Filters applied when discovering works in a source's catalog"""

    languages: list[str] | None = None
    book_ids: list[str] | None = None
    collections: list[str] | None = None


@dataclass(frozen=True, slots=True)
class WorkRef:
    """Lightweight reference to a work, before full metadata is fetched"""

    id: str
    source: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DownloadRequest:
    """Where to fetch one format of a work and where to put it"""

    url: str
    format_name: str
    target: Path | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class CatalogPort(ABC):
    """Discovers which works a source offers, given filters"""

    @abstractmethod
    def discover(self, filters: CatalogFilters) -> Iterable[WorkRef]: ...


class MetadataPort(ABC):
    """Fetches full metadata for discovered works"""

    @abstractmethod
    def fetch(self, refs: Iterable[WorkRef]) -> Iterable[Work]: ...


class FormatResolverPort(ABC):
    """Resolves a work + format name into a concrete download"""

    @abstractmethod
    def resolve(self, work: Work, format_name: str) -> DownloadRequest | None: ...


class RewriterPort(ABC):
    """Rewrites a work's HTML for offline use inside the ZIM"""

    @abstractmethod
    def rewrite_html(self, work: Work, html: BeautifulSoup) -> BeautifulSoup: ...


class CollectionMapperPort(ABC):
    """Maps a work to the collections (shelves, subjects, ...) it belongs to"""

    @abstractmethod
    def map(self, work: Work) -> list[CollectionRef]: ...
