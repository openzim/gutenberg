"""Ports (interfaces) between the source-agnostic core and a source.

Each source implements these interfaces; the pipeline only ever talks to the
abstractions. This is what keeps `core/` free of source-specific knowledge.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from gutenberg2zim.core.models import Work


@dataclass(frozen=True, slots=True)
class CatalogFilters:
    """Filters applied when discovering works in a source's catalog"""

    languages: list[str] | None = None
    book_ids: list[str] | None = None
    collections: list[str] | None = None
    formats: list[str] | None = None
    options: dict[str, Any] = field(default_factory=dict)


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
