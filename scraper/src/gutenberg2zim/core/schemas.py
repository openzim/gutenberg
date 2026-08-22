"""Pydantic schemas for JSON serialization with camelCase conversion"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Model to transform Python snake_case into JSON camelCase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


# Author Models
class Author(CamelModel):
    """Author information for JSON export"""

    id: str  # gut_id
    first_name: str | None = None
    last_name: str
    birth_year: str | None = None
    death_year: str | None = None
    name: str  # Formatted full name


class AuthorPreview(CamelModel):
    """Author preview for list views"""

    id: str
    name: str
    book_count: int
    total_popularity: int = 0


class AuthorDetail(AuthorPreview):
    """Full author details with books list"""

    first_name: str | None = None
    last_name: str
    birth_year: str | None = None
    death_year: str | None = None
    books: list[BookPreview]


# Book Models
class BookFormat(CamelModel):
    """Available format information"""

    format: str  # "html", "epub", "pdf"
    path: str  # ZIM path to file
    available: bool = True


class BookPreview(CamelModel):
    """Book preview for list views"""

    id: str  # source-specific work id (not necessarily numeric)
    title: str
    author: AuthorPreview
    languages: list[str]
    popularity: int  # Flame rating (0-3)
    cover_path: str | None = None
    primary_collection: str | None = None
    available_formats: list[str] = []
    description: str | None = None


class Book(BookPreview):
    """Full book details"""

    subtitle: str | None = None
    license: str
    primary_metric: int
    author: Author
    formats: list[BookFormat]
    description: str | None = None


# Collection Models
class Books(CamelModel):
    """List of book previews"""

    books: list[BookPreview]
    total_count: int


class Authors(CamelModel):
    """List of author previews"""

    authors: list[AuthorPreview]
    total_count: int


class CollectionPreview(CamelModel):
    """Collection preview for source-neutral collection views."""

    id: str
    name: str
    book_count: int
    total_popularity: int = 0


class Collection(CollectionPreview):
    """Collection detail with its works."""

    books: list[BookPreview]


class Collections(CamelModel):
    """List of collection previews."""

    collections: list[CollectionPreview]
    total_count: int


class SourceInfo(CamelModel):
    """Identity and description of the content source."""

    slug: str
    name: str
    description: str


class ThemeConfig(CamelModel):
    """Source-specific UI presentation settings."""

    primary_color: str | None = None
    secondary_color: str | None = None
    format_icons: dict[str, str]
    route_labels: dict[str, str]
    collection_icon_style: str = "classification"


class FeatureFlags(CamelModel):
    """Capabilities available to the UI."""

    epub_reader: bool
    pdf_reader: bool
    noscript_fallback: bool


class Config(CamelModel):
    """UI configuration"""

    title: str
    description: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    source: SourceInfo
    theme: ThemeConfig
    features: FeatureFlags


# Update forward references for Pydantic v2
BookPreview.model_rebuild()
Book.model_rebuild()
AuthorDetail.model_rebuild()
