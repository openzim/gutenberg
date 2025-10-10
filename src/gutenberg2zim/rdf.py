import re
import tarfile
from pathlib import Path
from tarfile import TarFile, TarInfo

from bs4 import BeautifulSoup, Tag

from gutenberg2zim.constants import logger
from gutenberg2zim.models import Author, Book, repository
from gutenberg2zim.scraper_progress import ScraperProgress
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


def parse_and_fill(
    rdf_path: Path, only_books: list[int], progress: ScraperProgress
) -> None:
    """Parse RDF files and populate the singleton BookRepository"""
    logger.info(f"\tExtracting RDF files for {len(only_books)} books from {rdf_path}")
    progress.increase_total(len(only_books))

    # Open the tar file for random access
    with tarfile.open(name=rdf_path, mode="r:bz2") as rdf_tarfile:
        for book_id in only_books:
            progress.increase_progress()

            # RDF files are organized as cache/epub/{book_id}/pg{book_id}.rdf
            rdf_member_path = f"cache/epub/{book_id}/pg{book_id}.rdf"

            try:
                rdf_member = rdf_tarfile.getmember(rdf_member_path)
            except KeyError:
                logger.warning(f"\tCould not find RDF file for book {book_id}")
                continue

            parse_and_process_file(rdf_tarfile, rdf_member)


def parse_and_process_file(rdf_tarfile: TarFile, rdf_member: TarInfo) -> None:
    member_match = re.match(r".*/pg([0-9]+).rdf", rdf_member.name)
    if not member_match:
        raise Exception(f"RDF member should match expected regex: {rdf_member.name}")
    gid = member_match.groups()[0]

    if repository.get_book(int(gid)):
        logger.debug(
            f"\tSkipping already parsed file {rdf_member.name} for book id {gid}"
        )
        return

    logger.debug(f"\tParsing file {rdf_member.name} for book id {gid}")
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
        save_rdf_in_repository(parser)


class RdfParser:
    def __init__(self, rdf_data, gid):
        self.rdf_data = rdf_data
        self.gid = gid

        self.author_id = None
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
        full_title = title.text if title else "- No Title -"
        title_elements = full_title.split("\n")
        self.title = title_elements[0]
        self.subtitle = " ".join(title_elements[1:])

        # Parsing for the bookshelf name
        bookshelf_tag = soup.find("pgterms:bookshelf")
        if bookshelf_tag:
            rdf_value = bookshelf_tag.find("rdf:value")
            if isinstance(rdf_value, Tag):  # pragma: no branch
                self.bookshelf = rdf_value.text

        # Search rdf to see if the image exists at the hard link
        # /cache/epub/{id}/pg{id}.cover.medium.jpg
        self.cover_image = (
            1
            if soup.find(
                "pgterms:file",
                attrs={
                    "rdf:about": lambda v: v
                    and v.endswith(
                        f"/cache/epub/{self.gid}/pg{self.gid}.cover.medium.jpg"
                    )
                },
            )
            else 0
        )

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
        author_tag = soup.find("dcterms:creator") or soup.find("marcrel:com")
        if author_tag:
            author_about_tag = author_tag.find("pgterms:agent")
            self.author_id = (
                author_about_tag.attrs["rdf:about"].split("/")[-1]
                if isinstance(author_about_tag, Tag)
                and "rdf:about" in getattr(author_about_tag, "attrs", "")
                else None
            )

            author_name_tag = author_tag.find("pgterms:name")
            if isinstance(author_name_tag, Tag):  # pragma: no branch
                author_name_elements = author_name_tag.text.split(",")

                if len(author_name_elements) > 1:
                    self.first_name = " ".join(
                        [element.strip() for element in author_name_elements[:0:-1]]
                    )
                self.last_name = author_name_elements[0]

        # Parsing the birth and (death, if the case) year of the author.
        # These values are likely to be null.
        self.birth_year = soup.find("pgterms:birthdate")
        self.birth_year = (
            get_formatted_number(self.birth_year.text) if self.birth_year else None
        )

        self.death_year = soup.find("pgterms:deathdate")
        self.death_year = (
            get_formatted_number(self.death_year.text) if self.death_year else None
        )

        # ISO 639-3 language codes that consist of 2 or 3 letters
        self.languages = [
            node.find("rdf:value").text
            for node in soup.find_all("dcterms:language")
            if node.find("rdf:value") is not None
        ]

        # The download count of the books on www.gutenberg.org.
        # This will be used to determine the popularity of the book.
        downloads_tag = soup.find("pgterms:downloads")
        if not isinstance(downloads_tag, Tag):
            raise Exception(f"Impossible to find download tag in book {self.gid} RDF")
        self.downloads = downloads_tag.text

        # The book might be licensed under GPL, public domain
        # or might be copyrighted
        license_tag = soup.find("dcterms:rights")
        if not isinstance(license_tag, Tag):
            raise Exception(f"Impossible to find license tag in book {self.gid} RDF")
        self.license = license_tag.text
        return self


def save_rdf_in_repository(parser: RdfParser) -> None:
    """Save parsed RDF data into the in-memory repository"""
    # Get or create author
    if parser.author_id:
        author = repository.get_author(parser.author_id)
        if not author:
            # Create new author
            normalized_last = normalize(parser.last_name) if parser.last_name else None
            author = Author(
                gut_id=parser.author_id,
                last_name=normalized_last or "Unknown",
                first_names=normalize(parser.first_name) if parser.first_name else None,
                birth_year=str(parser.birth_year) if parser.birth_year else None,
                death_year=str(parser.death_year) if parser.death_year else None,
            )
            repository.add_author(author)
        else:
            # Update existing author with new data
            if parser.last_name:
                normalized_last = normalize(parser.last_name)
                if normalized_last:
                    author.last_name = normalized_last
            if parser.first_name:
                author.first_names = normalize(parser.first_name)
            if parser.birth_year:
                author.birth_year = str(parser.birth_year)
            if parser.death_year:
                author.death_year = str(parser.death_year)
    else:
        # No author, use Anonymous (gut_id=216)
        author = repository.get_author("216")
        if not author:
            # Should not happen as repository initializes default authors
            author = Author(gut_id="216", last_name="Anonymous")
            repository.add_author(author)

    # Create or update book
    normalized_title = normalize(parser.title.strip()) if parser.title else "Untitled"
    book = Book(
        book_id=int(parser.gid),
        title=normalized_title if normalized_title else "Untitled",
        subtitle=normalize(parser.subtitle.strip()) if parser.subtitle else None,
        author=author,
        languages=[lang.strip() for lang in parser.languages],
        license=parser.license,
        downloads=int(parser.downloads),
        bookshelf=parser.bookshelf,
        cover_page=parser.cover_image,
    )
    repository.add_book(book)


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
