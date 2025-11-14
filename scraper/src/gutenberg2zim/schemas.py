"""Pydantic schemas for JSON serialization with camelCase conversion"""

from humps import camelize
from pydantic import BaseModel


class CamelModel(BaseModel):
    """Model to transform Python snake_case into JSON camelCase."""

    class Config:
        alias_generator = camelize
        populate_by_name = True


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


class AuthorDetail(CamelModel):
    """Full author details with books list"""

    id: str
    first_name: str | None = None
    last_name: str
    birth_year: str | None = None
    death_year: str | None = None
    name: str
    books: list["BookPreview"]
    book_count: int


# Book Models
class BookFormat(CamelModel):
    """Available format information"""

    format: str  # "html", "epub", "pdf"
    path: str  # ZIM path to file
    available: bool = True


class BookPreview(CamelModel):
    """Book preview for list views"""

    id: int
    title: str
    author: "AuthorPreview"
    languages: list[str]
    popularity: int  # Star rating (0-5)
    cover_path: str | None = None
    lcc_shelf: str | None = None


class Book(CamelModel):
    """Full book details"""

    id: int
    title: str
    subtitle: str | None = None
    author: "Author"
    languages: list[str]
    license: str
    downloads: int
    popularity: int
    lcc_shelf: str | None = None
    cover_path: str | None = None
    formats: list[BookFormat]
    description: str | None = None  # If available from RDF


# LCC Shelf Models
class LCCShelfPreview(CamelModel):
    """LCC shelf preview for list views"""

    code: str
    name: str | None = None
    book_count: int


class LCCShelf(CamelModel):
    """Full LCC shelf details"""

    code: str
    name: str | None = None
    books: list[BookPreview]
    book_count: int


# Collection Models
class Books(CamelModel):
    """List of book previews"""

    books: list[BookPreview]
    total_count: int


class Authors(CamelModel):
    """List of author previews"""

    authors: list[AuthorPreview]
    total_count: int


class LCCShelves(CamelModel):
    """List of LCC shelf previews"""

    shelves: list[LCCShelfPreview]
    total_count: int


class Config(CamelModel):
    """UI configuration"""

    title: str
    description: str | None = None
    main_color: str | None = None
    secondary_color: str | None = None


# Update forward references for Pydantic v2
BookPreview.model_rebuild()
Book.model_rebuild()
AuthorDetail.model_rebuild()
