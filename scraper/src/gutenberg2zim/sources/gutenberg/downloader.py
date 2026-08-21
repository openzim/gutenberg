"""In-memory download of Gutenberg book content (moved from `download.py`).

Per-book download orchestration on top of `GutenbergFormatResolver`: tries
the candidate mirror URLs for each requested format through the shared
`DownloadEngine` (per-thread sessions, retry with backoff), extracts zipped
HTML in memory and records formats that turn out to be unsupported.
"""

import io
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path

import requests

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import (
    DownloadEngine,
    is_fatal_http_error,
)
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.utils import (
    ALL_FORMATS,
    ensure_unicode,
    fname_for,
)
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.sources.gutenberg.catalog import GUTENBERG_SOURCE
from gutenberg2zim.sources.gutenberg.resolver import GutenbergFormatResolver


@dataclass
class BookContent:
    """In-memory storage for downloaded book content"""

    work: Work
    # Main content files keyed by filename
    files: dict[str, bytes] = field(default_factory=dict)
    # Cover image (if available)
    cover_image: bytes | None = None


def handle_zipped_html(zip_content: bytes, work: Work) -> dict[str, bytes]:
    """Extract HTML zip and return files as dict of filename -> bytes"""

    def clfn(fn):
        return Path(fn).name

    def is_safe(fname):
        name = ensure_unicode(clfn(fname))
        if fname == name:
            return True
        return fname == f"images/{name}"

    result_files = {}

    try:
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zf:
            # check that there is no insecure data (absolute names)
            if sum([1 for n in zf.namelist() if not is_safe(ensure_unicode(n))]):
                return {}

            zipped_files = zf.namelist()

            # is there multiple HTML files in ZIP ? (rare)
            mhtml = (
                sum(
                    [
                        1
                        for f in zipped_files
                        if f.endswith("html") or f.endswith(".htm")
                    ]
                )
                > 1
            )

            # Process all files from zip
            for zipped_file in zipped_files:
                # skip folders
                if zipped_file.endswith("/"):
                    continue

                fname = Path(zipped_file).name
                file_content = zf.read(zipped_file)

                if fname.endswith(".html") or fname.endswith(".htm"):
                    if mhtml:
                        if fname.startswith(f"{work.id}-h."):
                            result_files[f"{work.id}.html"] = file_content
                        else:
                            result_files[f"{work.id}_{fname}"] = file_content
                    else:
                        result_files[f"{work.id}.html"] = file_content
                else:
                    result_files[f"{work.id}_{fname}"] = file_content

    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError, zlib.error) as exc:
        # archive is unreadable when it should be a valid zip
        # (not a zip, encrypted, truncated, or corrupt deflate stream)
        logger.warning(f"Unreadable zip file for book #{work.id}: {exc}")
        return {}

    return result_files


def download_book(
    mirror_url: str,
    work: Work,
    formats: list[str],
    work_store: WorkStore,
    engine: DownloadEngine,
) -> BookContent | None:
    """Download a book in all requested formats and return in-memory content"""
    logger.debug(f"\tDownloading content files for Book #{work.id}")

    # apply filters (copy to avoid mutating caller's list or the global ALL_FORMATS)
    requested = list(formats or ALL_FORMATS)

    # HTML is our base for ZIM so add it if not present
    if "html" not in requested:
        requested.append("html")

    book_content = BookContent(work=work)
    resolver = GutenbergFormatResolver(mirror_url)
    unsupported_formats = work.extra.setdefault("unsupported_formats", [])

    for book_format in requested:
        logger.debug(f"Processing {book_format}")

        request = resolver.resolve(work, book_format)
        if request is None:
            # not supposed to happen, this is a bug
            raise RuntimeError(f"Unsupported {book_format} format for #{work.id}")

        downloaded = False
        for url in request.extra["candidate_urls"]:
            try:
                # retries transient errors itself; raises once exhausted
                # or immediately on a fatal HTTP status
                content_bytes = engine.fetch_bytes(url)
            except requests.RequestException as exc:
                # download failed: try next candidate URL
                # (4xx = the mirror just lacks this format: routine, debug only)
                if is_fatal_http_error(exc):
                    logger.debug(f"No {book_format} at {url} for #{work.id}")
                else:
                    logger.warning(f"Request failed for {url} of #{work.id}: {exc}")
                continue

            if url.endswith(".zip"):
                # extract zipfile in memory
                extracted_files = handle_zipped_html(
                    zip_content=content_bytes, work=work
                )
                if not extracted_files:
                    # ZIP was corrupt or rejected; try next preferred type
                    logger.warning(
                        f"ZIP extraction failed for {book_format} "
                        f"of #{work.id}, trying next type"
                    )
                    continue
                book_content.files.update(extracted_files)
            else:
                # Store the file directly
                filename = fname_for(work, book_format)
                book_content.files[filename] = content_bytes

            downloaded = True
            break

        if not downloaded:
            logger.debug(f"\t\tNo file available for {book_format} of #{work.id}")
            unsupported_formats.append(book_format)
            continue

    # delete book from DB if not downloaded in any format
    if all(fmt in unsupported_formats for fmt in requested):
        logger.warning(f"\t\tBook #{work.id} could not be downloaded in any format. ")
        work_store.remove(GUTENBERG_SOURCE, work.id)
        return None

    # Note: Cover image download moved to export_book to avoid downloading
    # when HTML already has a cover (see export.py)

    return book_content


def download_book_cover(
    mirror_url: str, work: Work, engine: DownloadEngine
) -> bytes | None:
    """Download cover image from mirror for a book.

    Returns cover image bytes if successful, None otherwise.
    """
    if not work.extra.get("has_cover"):
        logger.debug(f"No Book Cover found for Book #{work.id}")
        return None

    url = f"{mirror_url}/cache/epub/{work.id}/pg{work.id}.cover.medium.jpg"
    logger.debug(f"Downloading cover image from {url}")
    try:
        return engine.fetch_bytes(url)
    except requests.RequestException as exc:
        logger.warning(f"Failed to download cover for book #{work.id}: {exc}")
        return None
