from peewee import (
    CharField,
    DoesNotExist,
    ForeignKeyField,
    IntegerField,
    Model,
)
from playhouse.apsw_ext import APSWDatabase

from gutenberg2zim.constants import logger

timeout = 10
db = APSWDatabase(
    "gutenberg.db",
    pragmas=(
        ("journal_mode", "WAL"),
        ("cache_size", 10000),
        ("mmap_size", 1024 * 1024 * 32),
    ),
    timeout=timeout,
)
db.connect()
db.execute_sql("PRAGMA journal_mode=WAL;")


class BaseModel(Model):
    @classmethod
    def get_or_none(cls, *query, **kwargs):
        try:
            return cls.get(*query, **kwargs)
        except DoesNotExist:
            return None


class License(BaseModel):
    class Meta:
        database = db
        fixtures = (
            {"slug": "PD", "name": "Public domain in the USA."},
            {"slug": "None", "name": "None"},
            {
                "slug": "Copyright",
                "name": "Copyrighted. Read the copyright "
                "notice inside this book "
                "for details.",
            },
        )

    slug = CharField(max_length=20, primary_key=True)
    name = CharField()

    def __str__(self):
        return self.name


class Author(BaseModel):
    class Meta:
        database = db
        fixtures = (
            {
                "gut_id": "116",
                "last_name": "Various",
            },
            {
                "gut_id": "216",
                "last_name": "Anonymous",
            },
        )

    gut_id = CharField(primary_key=True, max_length=100)
    last_name = CharField(max_length=150)
    first_names = CharField(max_length=300, null=True)
    birth_year = CharField(max_length=10, null=True)
    death_year = CharField(max_length=10, null=True)

    def __str__(self):
        return self.name()

    def fname(self):
        return f"{self.name()}.{self.gut_id}"

    def name(self):
        def sanitize(text):
            return text.strip().replace("/", "-")[:230]

        if not self.first_names and not self.last_name:
            return sanitize("Anonymous")

        if not self.first_names:
            return sanitize(self.last_name)

        if not self.last_name:
            return sanitize(self.first_names)

        return sanitize(f"{self.first_names} {self.last_name}")

    def to_dict(self):
        return {
            "label": self.name(),
            "book_id": self.gut_id,
            "last_name": self.last_name,
            "first_names": self.first_names,
            "birth_year": self.birth_year,
            "death_year": self.death_year,
        }

    def to_array(self):
        return [
            self.name(),
            self.gut_id,
            # self.last_name,
            # self.first_names,
            # self.birth_year,
            # self.death_year,
        ]


class Book(BaseModel):
    class Meta:
        database = db

    book_id = IntegerField(primary_key=True)
    title = CharField(max_length=500)
    subtitle = CharField(max_length=500, null=True)
    author = ForeignKeyField(Author, related_name="books")
    book_license = ForeignKeyField(License, related_name="books")
    downloads = IntegerField(default=0)
    bookshelf = CharField(max_length=500, null=True)
    cover_page = IntegerField(default=0)
    popularity = 0

    html_etag = CharField(max_length=500, null=True)
    epub_etag = CharField(max_length=500, null=True)
    cover_etag = CharField(max_length=500, null=True)
    unsupported_formats = CharField(max_length=500, null=True)

    def __str__(self):
        return f"{self.book_id}/{self.title}/{self.bookshelf}"

    def to_dict(self):
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "author": self.author.name(),
            "license": self.book_license,
            "downloads": self.downloads,
            "bookshelf": self.bookshelf,
            "cover_page": self.cover_page,
        }

    def requested_formats(self, all_requested_formats):
        return [
            fmt
            for fmt in all_requested_formats
            if fmt not in str(self.unsupported_formats).split(",")
        ]

    def to_array(self, all_requested_formats):
        fmts = self.requested_formats(all_requested_formats)
        return [
            self.title,
            # self.subtitle,
            self.author.name(),
            # self.license,
            # self.language,
            # self.downloads
            "{html}{epub}{pdf}".format(
                html=int("html" in fmts),
                epub=int("epub" in fmts),
                pdf=int("pdf" in fmts),
            ),
            self.book_id,
            self.bookshelf,
        ]


def load_fixtures(model):
    logger.info(f"Loading fixtures for {model._meta.name}")

    for fixture in getattr(model._meta, "fixtures", []):
        f = model.create(**fixture)
        logger.debug(f"[fixtures] Created {f}")


def setup_database(*, wipe: bool = False) -> None:
    logger.info("Setting up the database")

    for model in (License, Author, Book, BookLanguage):
        if wipe:
            model.drop_table(fail_silently=True)
        if not model.table_exists():
            model.create_table()
            logger.debug(f"Created table for {model._meta.name}")  # type: ignore
            load_fixtures(model)
        else:
            logger.debug(f"{model._meta.name} table already exists.")  # type: ignore


class BookLanguage(BaseModel):
    class Meta:
        database = db

    book = ForeignKeyField(Book, backref="languages")
    language_code = CharField(max_length=10)

    def __str__(self):
        return f"{self.book.book_id} → {self.language_code}"
