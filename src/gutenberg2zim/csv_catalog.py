import csv
import gzip
import re
from dataclasses import dataclass
from pathlib import Path

from gutenberg2zim.constants import logger
from gutenberg2zim.utils import download_file


@dataclass
class CatalogEntry:
    """Catalog entry from CSV file"""

    book_id: int
    languages: list[str]
    lcc_shelf: str


def transform_locc_code(locc: str) -> str:
    """
    Transform LoCC code to shelf identifier.

    Rules:
    - Use only the first letter
    - Exception: if first letter is "P" and length > 2 and both characters are
      alphanum, use first two characters
    - Identifier is always uppercase

    Examples:
        "H" -> "H"
        "PR" -> "PR"
        "PS" -> "PS"
        "P" -> "P"
        "QA" -> "Q"
        "P12" -> "P"
        "b123" -> "B"
    """

    locc = locc.upper()

    if not locc:
        return ""

    locc = locc.strip()
    if not locc:
        return ""

    # If starts with P and length >= 2, use first two characters if both are alpha
    if (
        locc[0] == "P"
        and len(locc) >= 2  # noqa: PLR2004
        and re.match("[a-z]", locc[1], re.IGNORECASE)
    ):
        return locc[:2]

    # Otherwise, use only first character
    return locc[0]


def get_csv_fpath() -> Path:
    fname = "pg_catalog.csv.gz"
    fpath = Path(fname).resolve()
    return fpath


def download_csv_file(csv_path: Path, csv_url: str) -> None:
    """Download pg_catalog.csv.gz archive"""
    if csv_path.exists():
        logger.info(f"\tCSV catalog already exists in {csv_path}")
        return

    logger.info(f"\tDownloading {csv_url} into {csv_path}")
    download_file(csv_url, csv_path)


def load_catalog(csv_path: Path) -> list[CatalogEntry]:
    """
    Load catalog from CSV and return a list of catalog entries.

    Returns:
        list[CatalogEntry]: List of catalog entries with book_id, languages, and
          lcc_shelf
    """
    logger.info(f"\tLoading catalog from {csv_path}")
    catalog: list[CatalogEntry] = []

    with gzip.open(csv_path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                book_id = int(row["Text#"])
            except (ValueError, KeyError):
                logger.warning(f"Invalid book ID in row: {row.get('Text#', 'unknown')}")
                continue

            # Parse languages (can be multiple, semicolon-separated)
            languages_str = row.get("Language", "").strip()
            languages = [
                lang.strip() for lang in languages_str.split(";") if lang.strip()
            ]

            # Parse LoCC and transform to shelf identifier
            locc_str = row.get("LoCC", "").strip()
            lcc_shelf = transform_locc_code(locc_str) if locc_str else ""

            catalog.append(
                CatalogEntry(
                    book_id=book_id,
                    languages=languages,
                    lcc_shelf=lcc_shelf,
                )
            )

    logger.info(f"\tLoaded {len(catalog)} books from catalog")
    return catalog


def filter_books(
    catalog: list[CatalogEntry],
    languages: list[str] | None = None,
    only_books: list[int] | None = None,
    lcc_shelves: list[str] | None = None,
) -> list[int]:
    """
    Filter books based on languages, book IDs, and LCC shelves.

    Args:
        catalog: List of catalog entries
        languages: List of language codes to filter by (None = all languages)
        only_books: List of specific book IDs to include (None = all books)
        lcc_shelves: List of LCC shelf codes to filter by (None = all shelves,
                     empty list = all shelves)

    Returns:
        list: List of book IDs that match the filters
    """
    filtered: list[int] = []

    for entry in catalog:
        # Filter by specific book IDs if requested
        if only_books and entry.book_id not in only_books:
            continue

        # Filter by languages if requested
        if languages:
            # Check if any of the book's languages match requested languages
            if not any(lang in languages for lang in entry.languages):
                continue

        # Filter by LCC shelves if requested
        # None means don't filter by shelves
        # Empty list means include all shelves (generate all shelves)
        # Non-empty list means filter to only those shelves
        if lcc_shelves is not None and len(lcc_shelves) > 0:
            if entry.lcc_shelf not in lcc_shelves:
                continue

        filtered.append(entry.book_id)

    logger.info(
        f"\tFiltered to {len(filtered)} books "
        f"(languages: {languages or 'all'}, "
        f"specific books: {len(only_books) if only_books else 'all'}, "
        f"lcc_shelves: {lcc_shelves if lcc_shelves is not None else 'not filtering'})"
    )
    return filtered
