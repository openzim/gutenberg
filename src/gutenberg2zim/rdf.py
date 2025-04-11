import re
import tarfile
from pathlib import Path
from tarfile import TarFile, TarInfo

import peewee
from bs4 import BeautifulSoup

from gutenberg2zim.constants import logger
from gutenberg2zim.database import Author, Book, BookLanguage, License
from gutenberg2zim.utils import (
    download_file,
    normalize,
)


def get_rdf_fpath() -> Path:
    fname = "rdf-files.tar.bz2"
    fpath = Path(fname).resolve()
    return fpath


def download_rdf_file(rdf_path: Path, rdf_url: str) -> None:
    """Download rdf-files archive"""
    if rdf_path.exists():
        logger.info(f"\trdf-files archive already exists in {rdf_path}")
        return

    logger.info(f"\tDownloading {rdf_url} into {rdf_path}")
    download_file(rdf_url, rdf_path)


def parse_and_fill(rdf_path: Path, only_books: list[int]) -> None:
    logger.info(f"\tLooping throught RDF files in {rdf_path}")

    rdf_tarfile = tarfile.open(name=rdf_path, mode="r|bz2")

    for rdf_member in rdf_tarfile:
        rdf_member_path = Path(rdf_member.name)

        # skip books outside of requested list
        if (
            only_books
            and int(rdf_member_path.stem.replace("pg", "").replace(".rdf", ""))
            not in only_books
        ):
            continue

        if rdf_member_path.name == "pg0.rdf":
            continue

        if not rdf_member_path.name.endswith(".rdf"):
            continue

        parse_and_process_file(rdf_tarfile, rdf_member)


def parse_and_process_file(rdf_tarfile: TarFile, rdf_member: TarInfo) -> None:
    gid = re.match(r".*/pg([0-9]+).rdf", rdf_member.name).groups()[0]  # type: ignore

    if Book.get_or_none(book_id=int(gid)):
        logger.info(
            f"\tSkipping already parsed file {rdf_member.name} for book id {gid}"
        )
        return

    logger.info(f"\tParsing file {rdf_member.name} for book id {gid}")
    rdf_data = rdf_tarfile.extractfile(rdf_member)
    if rdf_data is None:
        logger.warning(
            f"Unable to extract member '{rdf_member.name}' from archive "
            f"'{rdf_member.name}'"
        )
        return

    parser = RdfParser(rdf_data.read(), gid).parse()

    if parser.license == "None":
        logger.info(f"\tWARN: Unusable book without any information {gid}")
    elif not parser.title:
        logger.info(f"\tWARN: Unusable book without title {gid}")
    else:
        save_rdf_in_database(parser)


class RdfParser:
    def __init__(self, rdf_data, gid):
        self.rdf_data = rdf_data
        self.gid = gid

        self.author_id = None
        self.author_name = None
        self.first_name = None
        self.last_name = None

        self.bookshelf = None
        self.cover_image = 0

    def parse(self):
        soup = BeautifulSoup(self.rdf_data, "lxml")

        # The tile of the book: this may or may not be divided
        # into a new-line-seperated title and subtitle.
        # If it is, then we will just split the title.
        title = soup.find("dcterms:title")
        self.title = title.text if title else "- No Title -"
        self.title = self.title.split("\n")[0]
        self.subtitle = " ".join(self.title.split("\n")[1:])
        self.author_id = None

        # Parsing for the bookshelf name
        self.bookshelf = soup.find("pgterms:bookshelf")
        if self.bookshelf:
            self.bookshelf = self.bookshelf.find("rdf:value").text  # type: ignore

        # Search rdf to see if the image exists at the hard link
        # https://www.gutenberg.ord/cache/epub/id/pg{id}.cover.medium.jpg
        if soup.find("cover.medium.jpg"):
            self.cover_image = 1

        # Parsing the name of the Author. Sometimes it's the name of
        # an organization or the name is not known and therefore
        # the <dcterms:creator> or <marcrel:com> node only return
        # "anonymous" or "unknown". For the case that it's only one word
        # `self.last_name` will be null.
        # Because of a rare edge case that the field of the parsed
        # author's name
        # has more than one comma we will join the first name in reverse,
        # starting
        # with the second item.
        self.author = soup.find("dcterms:creator") or soup.find("marcrel:com")
        if self.author:
            self.author_id = self.author.find("pgterms:agent")
            self.author_id = (
                self.author_id.attrs["rdf:about"].split("/")[-1]  # type: ignore
                if "rdf:about" in getattr(self.author_id, "attrs", "")
                else None
            )

            if self.author.find("pgterms:name"):
                self.author_name = self.author.find("pgterms:name")
                self.author_name = self.author_name.text.split(",")  # type: ignore

                if len(self.author_name) > 1:
                    self.first_name = " ".join(self.author_name[::-2]).strip()
                self.last_name = self.author_name[0]

        # Parsing the birth and (death, if the case) year of the author.
        # These values are likely to be null.
        self.birth_year = soup.find("pgterms:birthdate")
        self.birth_year = self.birth_year.text if self.birth_year else None
        self.birth_year = get_formatted_number(self.birth_year)

        self.death_year = soup.find("pgterms:deathdate")
        self.death_year = self.death_year.text if self.death_year else None
        self.death_year = get_formatted_number(self.death_year)

        # ISO 639-3 language codes that consist of 2 or 3 letters
        self.languages = [
            node.find("rdf:value").text  # type: ignore
            for node in soup.find_all("dcterms:language")
            if node.find("rdf:value") is not None  # type: ignore
        ]

        # The download count of the books on www.gutenberg.org.
        # This will be used to determine the popularity of the book.
        self.downloads = soup.find("pgterms:downloads").text  # type: ignore

        # The book might be licensed under GPL, public domain
        # or might be copyrighted
        self.license = soup.find("dcterms:rights").text  # type: ignore

        # Finding out all the file types this book is available in
        file_types = soup.find_all("pgterms:file")
        self.file_types = {}
        for x in file_types:
            if not x.find("rdf:value").text.endswith("application/zip"):
                k = x.attrs["rdf:about"].split("/")[-1]
                v = x.find("rdf:value").text
                self.file_types.update({k: v})

        return self


def get_or_create_author(parser: RdfParser) -> Author:
    # Insert author, if it not exists
    if parser.author_id:
        try:
            author_record = Author.get(gut_id=parser.author_id)
        except Exception:
            try:
                author_record = Author.create(
                    gut_id=parser.author_id,
                    last_name=normalize(parser.last_name),
                    first_names=normalize(parser.first_name),
                    birth_year=parser.birth_year,
                    death_year=parser.death_year,
                )
            # concurrent workers might colide here so we retry once on IntegrityError
            except peewee.IntegrityError:
                author_record = Author.get(gut_id=parser.author_id)
        else:
            if parser.last_name:
                author_record.last_name = normalize(parser.last_name)
            if parser.first_name:
                author_record.first_names = normalize(parser.first_name)
            if parser.birth_year:
                author_record.birth_year = parser.birth_year
            if parser.death_year:
                author_record.death_year = parser.death_year
            author_record.save()
    else:
        # No author, set Anonymous
        author_record = Author.get(gut_id="216")
    return author_record


def get_license(parser: RdfParser) -> License | None:
    # Get license
    try:
        return License.get(name=parser.license)
    except Exception:
        return None


def get_or_create_book(
    parser: RdfParser, author: Author, license_record: License | None
) -> Book:
    # Insert book
    try:
        book_record = Book.get(book_id=parser.gid)
    except peewee.DoesNotExist:
        book_record = Book.create(
            book_id=parser.gid,
            title=normalize(parser.title.strip()),
            subtitle=normalize(parser.subtitle.strip()),
            author=author,  # foreign key
            book_license=license_record,  # foreign key
            downloads=parser.downloads,
            bookshelf=parser.bookshelf,
            cover_page=parser.cover_image,
        )
    else:
        book_record.title = normalize(parser.title.strip())
        book_record.subtitle = normalize(parser.subtitle.strip())
        book_record.author = author  # foreign key
        book_record.book_license = license_record  # foreign key
        book_record.downloads = parser.downloads
        book_record.save()
    return book_record


def update_book_languages(book: Book, languages: list[str]) -> None:
    if not languages:
        return
    try:
        # delete old language records
        BookLanguage.delete().where(BookLanguage.book == book).execute()
        for lang in languages:
            BookLanguage.create(book=book, language_code=lang.strip())
    except Exception as e:
        logger.warning(f"Failed to update languages for book {book.book_id}: {e}")


def save_rdf_in_database(parser: RdfParser) -> None:
    author_record = get_or_create_author(parser)
    license_record = get_license(parser)
    book_record = get_or_create_book(parser, author_record, license_record)
    update_book_languages(book_record, parser.languages)


def get_formatted_number(num: str | None) -> str | None:
    """
    Get a formatted string of a number from a not-predictable-string
    that may or may not actually contain a number.
    Append a BC notation to the number num with, if the
    number is negative.
    returns: a formatted string of the number, or num if
             num is not negative or None.
    """
    if not num:
        return None
    if all(["-" in num, num.replace("-", "").strip().isdigit()]):
        return " ".join([num, "BC"])
    return num


if __name__ == "__main__":
    # Bacic Test with a sample rdf file
    nums = [f"{i:0=5d}" for i in range(21000, 40000)]
    for num in nums:
        logger.debug(f"Testing RDF: {num}")
        curd = Path(__file__).parent
        rdf = curd.parent / "rdf-files" / num / f"pg{num}.rdf"
        if rdf.is_file():
            data = ""
            with open(rdf) as f:
                data = f.read()

            parser = RdfParser(data, num).parse()
            logger.info(f"Parsed name: {parser.first_name} {parser.last_name}")
