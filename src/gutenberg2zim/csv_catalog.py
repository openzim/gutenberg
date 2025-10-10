import csv
import gzip
from pathlib import Path

from gutenberg2zim.constants import logger
from gutenberg2zim.utils import download_file


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


def load_catalog(csv_path: Path) -> dict[int, list[str]]:
    """
    Load catalog from CSV and return a dictionary mapping book_id to list of languages.

    Returns:
        dict: {book_id: [language_codes]}
    """
    logger.info(f"\tLoading catalog from {csv_path}")
    catalog: dict[int, list[str]] = {}

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

            catalog[book_id] = languages

    logger.info(f"\tLoaded {len(catalog)} books from catalog")
    return catalog


def filter_books(
    catalog: dict[int, list[str]],
    languages: list[str] | None = None,
    only_books: list[int] | None = None,
) -> list[int]:
    """
    Filter books based on languages and book IDs.

    Args:
        catalog: Dictionary mapping book_id to list of languages
        languages: List of language codes to filter by (None = all languages)
        only_books: List of specific book IDs to include (None = all books)

    Returns:
        list: List of book IDs that match the filters
    """
    filtered: list[int] = []

    for book_id, book_languages in catalog.items():
        # Filter by specific book IDs if requested
        if only_books and book_id not in only_books:
            continue

        # Filter by languages if requested
        if languages:
            # Check if any of the book's languages match requested languages
            if not any(lang in languages for lang in book_languages):
                continue

        filtered.append(book_id)

    logger.info(
        f"\tFiltered to {len(filtered)} books "
        f"(languages: {languages or 'all'}, "
        f"specific books: {len(only_books) if only_books else 'all'})"
    )
    return filtered
