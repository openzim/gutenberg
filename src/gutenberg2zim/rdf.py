from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

from gutenberg2zim.constants import DEFAULT_HTTP_TIMEOUT, logger
from gutenberg2zim.csv_catalog import transform_locc_code
from gutenberg2zim.models import Author, Book, repository
from gutenberg2zim.utils import normalize


class RdfParser:
    def __init__(self, rdf_data, gid):
        self.rdf_data = rdf_data
        self.gid = gid

        self.author_id = None
        self.first_name = None
        self.last_name = None

        self.bookshelf = None
        self.lcc_shelf = None
        self.cover_image = 0

    def parse(self):
        soup = BeautifulSoup(self.rdf_data, "lxml-xml")

        # The tile of the book: this may or may not be divided
        # into a new-line-seperated title and subtitle.
        # If it is, then we will just split the title.
        title = soup.find("dcterms:title")
        full_title = title.text if title else "- No Title -"
        title_elements = full_title.split("\n")
        self.title = title_elements[0]
        self.subtitle = " ".join(title_elements[1:])

        # Parsing for the bookshelf name (deprecated, kept for compatibility)
        bookshelf_tag = soup.find("pgterms:bookshelf")
        if bookshelf_tag:
            rdf_value = bookshelf_tag.find("rdf:value")
            if isinstance(rdf_value, Tag):  # pragma: no branch
                self.bookshelf = rdf_value.text

        # Parsing for the LoCC (Library of Congress Classification)
        # Transform it to a shelf identifier
        subject_tags = soup.find_all("dcterms:subject")
        for subject_tag in subject_tags:
            description = subject_tag.find("rdf:Description")
            if description:
                # Check if this is LCC by looking for the exact resource URL
                member_of = description.find("dcam:memberOf")
                if member_of:
                    resource = member_of.get("rdf:resource", "")
                    if resource == "http://purl.org/dc/terms/LCC":
                        value_tag = description.find("rdf:value")
                        if isinstance(value_tag, Tag):
                            locc_str = value_tag.text.strip()
                            self.lcc_shelf = transform_locc_code(locc_str)
                            break

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


def _save_rdf_in_repository(parser: RdfParser) -> None:
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
        lcc_shelf=parser.lcc_shelf,
        cover_page=parser.cover_image,
    )
    repository.add_book(book)


def download_and_parse_book_rdf(book_id: int, mirror_url: str) -> Book | None:
    """Download and parse RDF for a single book from the mirror.

    Args:
        book_id: The Gutenberg book ID
        mirror_url: The mirror URL (e.g., "https://gutenberg.mirror.driftle.ss")

    Returns:
        Book object if successful, None if book couldn't be downloaded or parsed
    """
    # Construct URL: {mirror_url}/cache/epub/{book_id}/pg{book_id}.rdf
    rdf_url = f"{mirror_url}/cache/epub/{book_id}/pg{book_id}.rdf"

    logger.debug(f"Downloading RDF for book {book_id} from {rdf_url}")

    try:
        response = requests.get(rdf_url, timeout=DEFAULT_HTTP_TIMEOUT)
        response.raise_for_status()
        rdf_data = response.content
    except requests.RequestException as exc:
        logger.warning(f"Could not download RDF for book {book_id}: {exc}")
        return None

    # Parse the RDF data
    try:
        parser = RdfParser(rdf_data, str(book_id)).parse()
    except Exception as exc:
        logger.warning(f"Could not parse RDF for book {book_id}: {exc}")
        return None

    # Validate the parsed data
    if parser.license == "None":
        logger.info(f"\tWARN: Unusable book without any information {book_id}")
        return None
    elif not parser.title:
        logger.info(f"\tWARN: Unusable book without title {book_id}")
        return None

    # Save to repository and return the book
    _save_rdf_in_repository(parser)
    return repository.get_book(book_id)


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
