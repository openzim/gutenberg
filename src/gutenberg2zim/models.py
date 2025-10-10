"""In-memory data models for Gutenberg books"""

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


@dataclass(unsafe_hash=True)
class Book:
    """Book metadata"""

    book_id: int
    title: str
    author: Author
    languages: list[str] = field(default_factory=list)
    license: str = "Public domain in the USA."
    subtitle: str | None = None
    downloads: int = 0
    bookshelf: str | None = None
    cover_page: int = 0
    unsupported_formats: list[str] = field(default_factory=list)
    popularity: int = 0  # Computed field for star rating

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
            self.bookshelf,
        ]


class BookRepository:
    """In-memory repository for books and authors (Singleton)"""

    _instance: "BookRepository | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Only initialize once
        if self._initialized:
            return
        self._initialized = True
        self.books: dict[int, Book] = {}
        self.authors: dict[str, Author] = {}
        self._init_default_authors()

    def _init_default_authors(self):
        """Initialize default authors (Various, Anonymous)"""
        self.authors["116"] = Author(gut_id="116", last_name="Various")
        self.authors["216"] = Author(gut_id="216", last_name="Anonymous")

    @classmethod
    def get_instance(cls) -> "BookRepository":
        """Get the singleton instance of BookRepository"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reset(self) -> None:
        """Reset the repository (useful for testing)"""
        self.books.clear()
        self.authors.clear()
        self._init_default_authors()

    def add_author(self, author: Author) -> Author:
        """Add or update author"""
        if author.gut_id in self.authors:
            # Update existing author
            existing = self.authors[author.gut_id]
            if author.last_name:
                existing.last_name = author.last_name
            if author.first_names:
                existing.first_names = author.first_names
            if author.birth_year:
                existing.birth_year = author.birth_year
            if author.death_year:
                existing.death_year = author.death_year
            return existing
        else:
            self.authors[author.gut_id] = author
            return author

    def get_author(self, gut_id: str) -> Author | None:
        """Get author by ID"""
        return self.authors.get(gut_id)

    def add_book(self, book: Book) -> None:
        """Add or update book"""
        self.books[book.book_id] = book

    def get_book(self, book_id: int) -> Book | None:
        """Get book by ID"""
        return self.books.get(book_id)

    def get_all_books(self) -> list[Book]:
        """Get filtered and sorted list of books"""
        return list(self.books.values())

    def get_languages_sorted_by_count(
        self, only_books: list[int] | None = None
    ) -> list[str]:
        """Get list of languages sorted by number of books (most used first)"""
        books = list(self.books.values())
        if only_books:
            books = [b for b in books if b.book_id in only_books]

        # Count books per language
        lang_counts: dict[str, int] = {}
        for book in books:
            for lang in book.languages:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

        # Sort by count (descending)
        return sorted(
            lang_counts.keys(), key=lambda lang: lang_counts[lang], reverse=True
        )

    def get_all_authors(self) -> list[Author]:
        """Get list of authors for the given books"""
        return list(self.authors.values())

    def get_bookshelves(self) -> list[str]:
        """Get unique list of bookshelves"""
        return sorted(
            {book.bookshelf for book in self.books.values() if book.bookshelf}
        )

    def remove_book(self, book_id: int) -> None:
        """Remove a book from the repository"""
        self.books.pop(book_id, None)


# Module-level singleton instance
repository = BookRepository.get_instance()
