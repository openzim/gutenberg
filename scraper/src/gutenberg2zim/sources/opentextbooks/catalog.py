"""Open Textbook Library catalog access backed by its cumulative CSV export."""

import csv
import io
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.language import ISO_MATRIX_REV
from gutenberg2zim.core.ports import (
    CatalogFilters,
    CatalogPort,
    DownloadRequest,
    WorkRef,
)
from gutenberg2zim.sources.opentextbooks.resolver import (
    FORMAT_TYPES,
    is_direct_file_url,
)

OTL_SOURCE = "opentextbooks"
CATALOG_FILENAME = "opentextbooks_catalog.csv"


def _numbered_column_suffixes(
    row: dict[str | None, str | None], prefix: str
) -> list[str]:
    """Return numeric suffixes for CSV columns named like ``Type 1``."""
    return sorted(
        (
            suffix
            for column in row
            if isinstance(column, str)
            and column.startswith(prefix)
            and (suffix := column.removeprefix(prefix)).isdigit()
        ),
        key=int,
    )


def normalize_language(code: str | None) -> str | None:
    """OTL uses ISO 639-2 codes ("eng"); the pipeline uses 2-letter codes."""
    return ISO_MATRIX_REV.get(code, code) if code else None


@dataclass(frozen=True, slots=True)
class OtlCatalogEntry:
    """CSV data used for selection and as metadata fallbacks."""

    book_id: str
    title: str
    description: str | None
    license: str | None
    source_url: str | None
    isbn10: str | None
    isbn13: str | None
    copyright_year: str | None
    formats: tuple[tuple[str, str], ...]
    subjects: tuple[str, ...]


class OpenTextbookLibraryCatalog(CatalogPort):
    """Discover downloadable OTL textbooks from a locally cached CSV catalog."""

    BASE_URL = "https://open.umn.edu/opentextbooks"

    def __init__(
        self,
        engine: DownloadEngine,
        base_url: str = BASE_URL,
        cache_dir: Path | None = None,
        *,
        refresh_catalog: bool = False,
        **_: object,
    ):
        self._engine = engine
        self._base_url = base_url.rstrip("/")
        self._csv_path = cache_dir.resolve() / CATALOG_FILENAME if cache_dir else None
        self._refresh_catalog = refresh_catalog

    def discover(self, filters: CatalogFilters) -> Iterable[WorkRef]:
        entries = self._load_catalog()
        requested_formats = set(filters.formats or FORMAT_TYPES)
        downloadable = [
            entry
            for entry in entries
            if self._has_requested_format(entry, requested_formats)
        ]
        requested_subjects = {
            subject.casefold() for subject in filters.options.get("subjects", [])
        }
        if requested_subjects:
            downloadable = [
                entry
                for entry in downloadable
                if requested_subjects.intersection(
                    subject.casefold() for subject in entry.subjects
                )
            ]

        source_book_ids = set(filters.options.get("book_ids", []))
        positions = {int(book_id) for book_id in filters.book_ids or []}
        if source_book_ids:
            selected = [
                entry for entry in downloadable if entry.book_id in source_book_ids
            ]
        elif positions:
            selected = [
                entry
                for position, entry in enumerate(downloadable, start=1)
                if position in positions
            ]
        else:
            selected = downloadable

        logger.info(
            "  Selected %s downloadable OTL books from %s catalog entries"
            " (subjects: %s)",
            len(selected),
            len(entries),
            filters.options.get("subjects") or "all",
        )
        # The CSV does not have a language column. OTL is predominantly English;
        # full JSON metadata is fetched later for each selected work.
        return [
            WorkRef(
                id=entry.book_id,
                source=OTL_SOURCE,
                extra={
                    "languages": ["en"],
                    "title": entry.title,
                    "description": entry.description,
                    "license": entry.license,
                    "source_url": entry.source_url,
                    "isbn10": entry.isbn10,
                    "isbn13": entry.isbn13,
                    "copyright_year": entry.copyright_year,
                    "formats": entry.formats,
                    "subjects": entry.subjects,
                },
            )
            for entry in selected
        ]

    def list_subjects(self) -> list[str]:
        """Return every subject published in the OTL CSV catalog."""
        return sorted(
            {subject for entry in self._load_catalog() for subject in entry.subjects},
            key=str.casefold,
        )

    def refresh(self) -> None:
        """Refresh the locally cached catalog without selecting any books."""
        self._load_catalog()

    def _load_catalog(self) -> list[OtlCatalogEntry]:
        url = f"{self._base_url}/download.csv"
        if self._csv_path is None:
            logger.info("Downloading OTL CSV catalog from %s", url)
            csv_text = self._engine.fetch_bytes(url).decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(csv_text))
        elif self._refresh_catalog or not self._csv_path.exists():
            logger.info(
                "%s OTL CSV catalog from %s",
                "Refreshing" if self._csv_path.exists() else "Downloading",
                url,
            )
            self._engine.download(
                DownloadRequest(url=url, format_name="csv"), dest=self._csv_path
            )
            csv_text = self._csv_path.read_text(encoding="utf-8-sig")
            reader = csv.DictReader(io.StringIO(csv_text))
        else:
            logger.info("Using cached OTL CSV catalog at %s", self._csv_path)
            csv_text = self._csv_path.read_text(encoding="utf-8-sig")
            reader = csv.DictReader(io.StringIO(csv_text))

        entries: list[OtlCatalogEntry] = []
        for row in reader:
            book_id = row.get("Otl id", "").strip()
            if not book_id:
                continue
            formats = tuple(
                (
                    row.get(f"Type {suffix}", "").strip(),
                    row.get(f"URL {suffix}", "").strip(),
                )
                for suffix in _numbered_column_suffixes(row, "Type ")
                if row.get(f"Type {suffix}") and row.get(f"URL {suffix}")
            )
            subjects = tuple(
                subject
                for suffix in _numbered_column_suffixes(row, "Subject ")
                if (subject := row.get(f"Subject {suffix}", "").strip())
            )
            entries.append(
                OtlCatalogEntry(
                    book_id=book_id,
                    title=row.get("Title", "").strip(),
                    description=row.get("Description", "").strip() or None,
                    license=row.get("License", "").strip() or None,
                    source_url=row.get("Library URL", "").strip() or None,
                    isbn10=row.get("ISBN10", "").strip() or None,
                    isbn13=row.get("ISBN13", "").strip() or None,
                    copyright_year=row.get("Copyright year", "").strip() or None,
                    formats=formats,
                    subjects=subjects,
                )
            )
        return entries

    @staticmethod
    def _has_requested_format(entry: OtlCatalogEntry, formats: set[str]) -> bool:
        for format_name in formats:
            wanted = FORMAT_TYPES.get(format_name)
            if not wanted:
                continue
            otl_type, extension = wanted
            # Online editions are useful once a work is selected, but cannot
            # safely broaden default discovery: the catalog contains many
            # publisher landing pages rather than complete textbook editions.
            if extension is None:
                continue
            if any(
                source_type == otl_type and is_direct_file_url(url, extension)
                for source_type, url in entry.formats
            ):
                return True
        return False
