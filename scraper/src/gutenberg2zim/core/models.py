"""Source-agnostic domain model.

These dataclasses describe any book-like "work" independently of the source
it came from. Source-specific code converts its own metadata into these models;
everything downstream (storage, export, ZIM assembly) only ever sees these types.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class Creator:
    id: str
    name: str
    sort_name: str | None = None
    birth_date: int | None = None
    death_date: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Format:
    name: str
    media_type: str
    url: str | None = None
    local_path: str | None = None
    size: int | None = None


@dataclass(frozen=True, slots=True)
class Cover:
    source_url: str | None = None
    local_path: str | None = None
    alt: str | None = None


@dataclass(frozen=True, slots=True)
class CollectionRef:
    id: str
    name: str
    kind: str = "collection"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Work:
    id: str
    source: str
    title: str
    subtitle: str | None = None
    creators: list[Creator] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    license: str | None = None
    formats: list[Format] = field(default_factory=list)
    cover: Cover | None = None
    collections: list[CollectionRef] = field(default_factory=list)
    popularity: int | None = None
    primary_metric: int | None = None
    description: str | None = None
    published: date | None = None
    source_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
