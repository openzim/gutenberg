"""Gutenberg metadata access (moved from `gutenberg2zim.rdf`).

Downloads and parses the per-book RDF dumps and exposes them through the
source-agnostic `MetadataPort` interface.
"""

import re
from collections.abc import Iterable

from bs4 import BeautifulSoup, Tag

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import DownloadEngine, fetch_bytes_with_retry
from gutenberg2zim.core.models import CollectionRef, Cover, Creator, Work
from gutenberg2zim.core.ports import DownloadRequest, MetadataPort, WorkRef
from gutenberg2zim.core.utils import normalize
from gutenberg2zim.sources.gutenberg.catalog import (
    GUTENBERG_SOURCE,
    LCC_SHELF_KIND,
    transform_locc_code,
)

# Gutenberg's creator id for "Anonymous" in their RDF catalog
ANONYMOUS_CREATOR_ID = "216"


class RdfParseError(RuntimeError):
    """Raised when a book RDF file cannot be parsed"""


class RdfParser:
    def __init__(self, rdf_data, gid):
        self.rdf_data = rdf_data
        self.gid = gid

        self.author_id = None
        self.first_name = None
        self.last_name = None

        self.bookshelf = None
        self.lcc_shelf = None
        self.has_cover = False
        self.description = None
        self.birth_year: str | None = None
        self.death_year: str | None = None

    def parse(self):
        soup = BeautifulSoup(self.rdf_data, "lxml-xml")

        # Parse and clean the book title
        # Title may be divided into newline-separated title and subtitle
        title = soup.find("dcterms:title")
        full_title = clean_marc_notation(title.text) if title else ""
        title_elements = full_title.split("\n")
        self.title = title_elements[0]
        self.subtitle = " ".join(title_elements[1:])

        # Parsing for the bookshelf name (deprecated, kept for compatibility)
        bookshelf_tag = soup.find("pgterms:bookshelf")
        if bookshelf_tag:
            rdf_value = bookshelf_tag.find("rdf:value")
            if isinstance(rdf_value, Tag):  # pragma: no branch
                self.bookshelf = clean_marc_notation(rdf_value.text)

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
        def is_cover_node(node: Tag):
            if not node:
                return False
            for about_value in node.get_attribute_list("rdf:about"):
                if about_value.endswith(
                    f"/cache/epub/{self.gid}/pg{self.gid}.cover.medium.jpg"
                ):
                    return True
            return False

        self.has_cover = any(
            is_cover_node(file_node) for file_node in soup.find_all("pgterms:file")
        )

        # Parse book description (MARC 520 = summary)
        marc520_tag = soup.find("pgterms:marc520")
        if isinstance(marc520_tag, Tag):
            self.description = clean_marc_notation(marc520_tag.text)

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
                author_about_tag.get_attribute_list("rdf:about")[0].split("/")[-1]
                if isinstance(author_about_tag, Tag)
                and "rdf:about" in getattr(author_about_tag, "attrs", "")
                else None
            )

            author_name_tag = author_tag.find("pgterms:name")
            if isinstance(author_name_tag, Tag):  # pragma: no branch
                author_name = clean_marc_notation(author_name_tag.text)
                author_name_elements = author_name.split(",")

                if len(author_name_elements) > 1:
                    self.first_name = " ".join(
                        [element.strip() for element in author_name_elements[:0:-1]]
                    )
                self.last_name = author_name_elements[0]

        # Parsing the birth and (death, if the case) year of the author.
        # These values are likely to be null.
        birthdate_tag = soup.find("pgterms:birthdate")
        self.birth_year = (
            get_formatted_number(birthdate_tag.text) if birthdate_tag else None
        )

        deathdate_tag = soup.find("pgterms:deathdate")
        self.death_year = (
            get_formatted_number(deathdate_tag.text) if deathdate_tag else None
        )

        # ISO 639-3 language codes that consist of 2 or 3 letters
        self.languages = [
            val.text
            for node in soup.find_all("dcterms:language")
            if (val := node.find("rdf:value")) is not None
        ]

        # The download count of the books on www.gutenberg.org.
        # This will be used to determine the popularity of the book.
        downloads_tag = soup.find("pgterms:downloads")
        if not isinstance(downloads_tag, Tag):
            raise RdfParseError(
                f"Impossible to find download tag in book {self.gid} RDF"
            )
        self.downloads = downloads_tag.text

        # The book might be licensed under GPL, public domain
        # or might be copyrighted
        license_tag = soup.find("dcterms:rights")
        if not isinstance(license_tag, Tag):
            raise RdfParseError(
                f"Impossible to find license tag in book {self.gid} RDF"
            )
        self.license = license_tag.text
        return self


def clean_marc_notation(text: str) -> str:
    """
    Remove MARC (Machine-Readable Cataloging) notation from text.

    MARC uses subfield delimiters like $a, $b, $c, etc.
    Example: "Peter Pan $b [Peter and Wendy]" -> "Peter Pan [Peter and Wendy]"

    Args:
        text: The text potentially containing MARC notation

    Returns:
        Text with MARC subfield delimiters removed
    """
    return re.sub(r"\$[a-z]\s*", "", text) if text else text


def format_author_name(last_name: str | None, first_names: str | None) -> str:
    """Formatted author name, sanitized for use as a filename component"""

    def sanitize(text: str) -> str:
        return text.strip().replace("/", "-")[:230]

    if not first_names and not last_name:
        return sanitize("Anonymous")

    if not first_names:
        return sanitize(str(last_name))

    if not last_name:
        return sanitize(first_names)

    return sanitize(f"{first_names} {last_name}")


def _parse_year(value: str | None) -> int | None:
    """Parse a year from a raw string field, None if missing or not numeric"""
    if value and value.strip().isdigit():
        return int(value.strip())
    return None


def _work_from_parser(parser: RdfParser) -> Work:
    """Build a Work from a parsed RDF"""
    creators = []
    if parser.author_id:
        last_name = normalize(parser.last_name) if parser.last_name else None
        first_names = normalize(parser.first_name) if parser.first_name else None
        creators.append(
            Creator(
                id=parser.author_id,
                name=format_author_name(last_name or "Unknown", first_names),
                sort_name=last_name,
                birth_date=_parse_year(parser.birth_year),
                death_date=_parse_year(parser.death_year),
                extra={
                    "first_names": first_names,
                    "birth_year_raw": parser.birth_year,
                    "death_year_raw": parser.death_year,
                },
            )
        )
    else:
        # No author, use Anonymous
        creators.append(
            Creator(id=ANONYMOUS_CREATOR_ID, name="Anonymous", sort_name="Anonymous")
        )

    collections = []
    if parser.lcc_shelf:
        collections.append(
            CollectionRef(
                id=parser.lcc_shelf, name=parser.lcc_shelf, kind=LCC_SHELF_KIND
            )
        )

    normalized_title = normalize(parser.title.strip()) if parser.title else "Untitled"
    return Work(
        id=str(parser.gid),
        source=GUTENBERG_SOURCE,
        title=normalized_title if normalized_title else "Untitled",
        subtitle=normalize(parser.subtitle.strip()) if parser.subtitle else None,
        creators=creators,
        languages=[lang.strip() for lang in parser.languages],
        license=parser.license,
        cover=Cover() if parser.has_cover else None,
        collections=collections,
        popularity=0,
        primary_metric=int(parser.downloads),
        description=(
            normalize(parser.description.strip()) if parser.description else None
        ),
        extra={
            "unsupported_formats": [],
            "has_cover": parser.has_cover,
        },
    )


def fetch_book_metadata(
    book_id: int, mirror_url: str, engine: DownloadEngine | None = None
) -> Work | None:
    """Download and parse RDF for a single book from the mirror.

    Args:
        book_id: The Gutenberg book ID
        mirror_url: The mirror URL (e.g., "https://aleph.pglaf.org")
        engine: Optional DownloadEngine; when configured with a cache directory,
            RDF responses are cached on disk by URL hash. Otherwise it performs
            a plain in-memory fetch.

    Returns:
        Work if successful, None only for expected unusable books
        (no license, no title, etc.)

    Raises:
        requests.RequestException: If RDF download fails (retries handled by caller)
        RdfParseError: If RDF parsing fails
    """
    rdf_url = f"{mirror_url}/cache/epub/{book_id}/pg{book_id}.rdf"

    logger.debug(f"Downloading RDF for book {book_id} from {rdf_url}")

    if engine is not None and engine.cache_enabled:
        # cached on disk by URL hash; cache hits return without any HTTP call
        rdf_data = engine.download(
            DownloadRequest(url=rdf_url, format_name="rdf")
        ).path.read_bytes()
    elif engine is not None:
        rdf_data = engine.fetch_bytes(rdf_url)
    else:
        # Plain fetch (no disk cache); retry is per-download, errors bubble up
        rdf_data = fetch_bytes_with_retry(rdf_url)

    parser = RdfParser(rdf_data, str(book_id)).parse()

    # Skip books that are missing critical information
    if parser.license == "None":
        logger.info(f"\tWARN: Unusable book without any information {book_id}")
        return None
    elif not parser.title:
        logger.info(f"\tWARN: Unusable book without title {book_id}")
        return None

    return _work_from_parser(parser)


class GutenbergRdfMetadata(MetadataPort):
    """`MetadataPort` implementation backed by the Gutenberg RDF dumps"""

    def __init__(self, mirror_url: str, engine: DownloadEngine | None = None):
        self._mirror_url = mirror_url
        self._engine = engine

    def fetch(self, refs: Iterable[WorkRef]) -> Iterable[Work]:
        works = []
        for ref in refs:
            work = fetch_book_metadata(int(ref.id), self._mirror_url, self._engine)
            if work is not None:
                works.append(work)
        return works


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
