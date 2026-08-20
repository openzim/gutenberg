"""Gutenberg book/author data models.

These are the Gutenberg-flavored records produced by the RDF metadata
parser and consumed by the exporters and Jinja templates. They predate the
core domain model (`core.models.Work`/`Creator`); `adapters.py` converts
between the two. Storage is handled by `core.work_store.WorkStore` (the old
`BookRepository` singleton was removed in the multi-source refactor).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(unsafe_hash=True)
class Author:
    """Author information"""

    gut_id: str
    last_name: str
    first_names: str | None = None
    birth_year: str | None = None
    death_year: str | None = None

    def name(self) -> str:
        """Get formatted author name"""

        def sanitize(text: str) -> str:
            return text.strip().replace("/", "-")[:230]

        if not self.first_names and not self.last_name:
            return sanitize("Anonymous")

        if not self.first_names:
            return sanitize(self.last_name)

        if not self.last_name:
            return sanitize(self.first_names)

        return sanitize(f"{self.first_names} {self.last_name}")

    def fname(self) -> str:
        """Get filename-safe author name with ID"""
        return f"{self.name()}.{self.gut_id}"

    def to_array(self) -> list:
        """Convert author to array format for templates"""
        return [
            self.name(),
            self.gut_id,
        ]

    def to_dict(self) -> dict:
        """Convert author to dictionary for JSON serialization"""
        return {
            "id": self.gut_id,
            "first_name": self.first_names,
            "last_name": self.last_name,
            "birth_year": self.birth_year,
            "death_year": self.death_year,
            "name": self.name(),
        }


@dataclass
class Book:
    """Book metadata"""

    book_id: int
    title: str
    author: Author
    languages: list[str] = field(default_factory=list)
    license: str = "Public domain in the USA."
    subtitle: str | None = None
    downloads: int = 0
    lcc_shelf: str | None = None
    has_cover: bool = False
    description: str | None = None
    unsupported_formats: list[str] = field(default_factory=list)
    popularity: int = 0  # Computed field for flame rating
    html_cover_path: str | None = None  # Path to cover image extracted from HTML
    _cover_href: str | None = None  # Original href from <link rel="icon"> for detection

    def requested_formats(self, all_requested_formats: list[str]) -> list[str]:
        """Get list of formats available for this book"""
        return [
            fmt for fmt in all_requested_formats if fmt not in self.unsupported_formats
        ]

    def to_array(self, all_requested_formats: list[str]) -> list:
        """Convert book to array format for templates"""
        fmts = self.requested_formats(all_requested_formats)
        return [
            self.title,
            self.author.name(),
            "{html}{epub}{pdf}".format(
                html=int("html" in fmts),
                epub=int("epub" in fmts),
                pdf=int("pdf" in fmts),
            ),
            self.book_id,
            self.lcc_shelf,
        ]

    def to_dict(self) -> dict:
        """Convert book to dictionary for JSON serialization (basic fields only)"""
        return {
            "id": self.book_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "languages": self.languages,
            "license": self.license,
            "downloads": self.downloads,
            "popularity": self.popularity,
            "lcc_shelf": self.lcc_shelf,
        }
