from peewee import (
    BooleanField,
    CharField,
    DoesNotExist,
    ForeignKeyField,
    IntegerField,
    Model,
    TextField,
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

    def __unicode__(self):
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

    def __unicode__(self):
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
            "id": self.gut_id,
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

    id = IntegerField(primary_key=True)  # noqa: A003
    title = CharField(max_length=500)
    subtitle = CharField(max_length=500, null=True)
    author = ForeignKeyField(Author, related_name="books")
    license = ForeignKeyField(License, related_name="books")  # noqa: A003
    language = CharField(max_length=10)
    downloads = IntegerField(default=0)
    bookshelf = CharField(max_length=500, null=True)
    cover_page = IntegerField(default=0)
    popularity = 0
    html_etag = CharField(max_length=500, null=True)
    epub_etag = CharField(max_length=500, null=True)
    cover_etag = CharField(max_length=500, null=True)

    def __unicode__(self):
        return f"{self.id}/{self.title}/{self.bookshelf}"

    def to_dict(self):
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "author": self.author.name(),
            "license": self.license,
            "language": self.language,
            "downloads": self.downloads,
            "bookshelf": self.bookshelf,
            "cover_page": self.cover_page,
        }

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
            self.id,
            self.bookshelf,
        ]

    def formats(self):
        from gutenberg2zim.utils import main_formats_for

        return main_formats_for(self)

    def requested_formats(self, all_requested_formats):
        fmts = self.formats()
        requested_formats = [fmt for fmt in fmts if fmt in all_requested_formats]
        return requested_formats


class BookFormat(BaseModel):
    class Meta:
        database = db

    book = ForeignKeyField(Book, related_name="bookformats")
    mime = CharField(max_length=100)
    images = BooleanField(default=True)
    pattern = CharField(max_length=100)
    downloaded_from = CharField(max_length=300, null=True)

    def __unicode__(self):
        return f"[{self.mime}] {self.book.title}"


class Url(BaseModel):
    class Meta:
        database = db

    url = TextField(index=True)

    def __unicode__(self):
        return self.url


def load_fixtures(model):
    logger.info(f"Loading fixtures for {model._meta.name}")

    for fixture in getattr(model._meta, "fixtures", []):
        f = model.create(**fixture)
        logger.debug(f"[fixtures] Created {f}")


def setup_database(*, wipe=False):
    logger.info("Setting up the database")

    for model in (License, Author, Book, BookFormat, Url):
        if wipe:
            model.drop_table(fail_silently=True)
        if not model.table_exists():
            model.create_table()
            logger.debug(f"Created table for {model._meta.name}")  # type: ignore
            load_fixtures(model)
        else:
            logger.debug(f"{model._meta.name} table already exists.")  # type: ignore
