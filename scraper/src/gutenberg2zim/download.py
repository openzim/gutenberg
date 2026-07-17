import io
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import requests

from gutenberg2zim.constants import (
    DEFAULT_HTTP_TIMEOUT,
    DL_CHUNCK_SIZE,
    logger,
)
from gutenberg2zim.models import Book, repository
from gutenberg2zim.pg_archive_urls import url_for_type
from gutenberg2zim.utils import (
    ALL_FORMATS,
    ensure_unicode,
    fname_for,
)

# map of preferred document type for every format
PG_PREFERRED_TYPES = {
    "html": ["zip", "html.images", "html.noimages"],
    "epub": ["epub3.images", "epub.images", "epub.noimages"],
    "pdf": ["pdf.images", "pdf.noimages"],
}


@dataclass
class BookContent:
    """In-memory storage for downloaded book content"""

    book: Book
    # Main content files keyed by filename
    files: dict[str, bytes] = field(default_factory=dict)
    # Cover image (if available)
    cover_image: bytes | None = None


def resource_exists(url):
    try:
        with requests.get(url, stream=True, timeout=DEFAULT_HTTP_TIMEOUT) as r:
            return r.status_code == requests.codes.ok
    except Exception as exc:
        logger.error(f"Exception occurred while testing {url}\n {exc}")
        return False


def handle_zipped_html(zip_content: bytes, book: Book) -> dict[str, bytes]:
    """Extract HTML zip and return files as dict of filename -> bytes"""

    def clfn(fn):
        return Path(fn).name

    def is_safe(fname):
        name = ensure_unicode(clfn(fname))
        if Path(fname).name == name:
            return True
        return fname == f"images/{Path(fname).name}"

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
                        if fname.startswith(f"{book.book_id}-h."):
                            result_files[f"{book.book_id}.html"] = file_content
                        else:
                            result_files[f"{book.book_id}_{fname}"] = file_content
                    else:
                        result_files[f"{book.book_id}.html"] = file_content
                else:
                    result_files[f"{book.book_id}_{fname}"] = file_content

    except zipfile.BadZipfile:
        # file is not a zip file when it should be.
        logger.warning(f"Bad zip file for book #{book.book_id}")
        return {}

    return result_files


def download_book(
    mirror_url: str,
    book: Book,
    formats: list[str],
) -> BookContent | None:
    """Download a book in all requested formats and return in-memory content"""
    logger.debug(f"\tDownloading content files for Book #{book.book_id}")

    # apply filters (copy to avoid mutating caller's list or the global ALL_FORMATS)
    requested_formats = list(formats or ALL_FORMATS)

    # HTML is our base for ZIM so add it if not present
    if "html" not in requested_formats:
        requested_formats.append("html")

    book_content = BookContent(book=book)

    for book_format in requested_formats:
        logger.debug(f"Processing {book_format}")

        pg_type_to_use = None
        url = None
        for pg_type in PG_PREFERRED_TYPES[book_format]:
            url = url_for_type(
                pg_type=pg_type, book_id=book.book_id, mirror_url=mirror_url
            )
            if not url:
                # not supposed to happen, this is a bug
                raise Exception(
                    f"Unsupported {pg_type} pg_type for {book_format} #{book.book_id}"
                )

            with requests.get(
                url, stream=True, timeout=DEFAULT_HTTP_TIMEOUT
            ) as pg_resp:  # in seconds
                if pg_resp.status_code == requests.codes.ok:
                    # Download content to memory
                    content_buffer = io.BytesIO()
                    for chunk in pg_resp.iter_content(chunk_size=DL_CHUNCK_SIZE):
                        if chunk:
                            content_buffer.write(chunk)
                    content_bytes = content_buffer.getvalue()

                    if url.endswith(".zip"):
                        # extract zipfile in memory
                        extracted_files = handle_zipped_html(
                            zip_content=content_bytes, book=book
                        )
                        if not extracted_files:
                            # ZIP was corrupt or rejected; try next preferred type
                            logger.warning(
                                f"ZIP extraction failed for {book_format} "
                                f"of #{book.book_id}, trying next type"
                            )
                            continue
                        book_content.files.update(extracted_files)
                    else:
                        # Store the file directly
                        filename = fname_for(book, book_format)
                        book_content.files[filename] = content_bytes

                    pg_type_to_use = pg_type
                    break

        if not url or not pg_type_to_use:
            logger.debug(f"\t\tNo file available for {book_format} of #{book.book_id}")
            book.unsupported_formats.append(book_format)
            continue

    # delete book from DB if not downloaded in any format
    if all(fmt in book.unsupported_formats for fmt in requested_formats):
        logger.warning(
            f"\t\tBook #{book.book_id} could not be downloaded in any format. "
        )
        repository.remove_book(book.book_id)
        return None

    # Note: Cover image download moved to export_book to avoid downloading
    # when HTML already has a cover (see export.py)

    return book_content


def download_book_cover(mirror_url: str, book: Book) -> bytes | None:
    """Download cover image from mirror for a book.

    Returns cover image bytes if successful, None otherwise.
    """
    if not book.has_cover:
        logger.debug(f"No Book Cover found for Book #{book.book_id}")
        return None

    url = f"{mirror_url}/cache/epub/{book.book_id}/pg{book.book_id}.cover.medium.jpg"
    logger.debug(f"Downloading cover image from {url}")
    try:
        with requests.get(url, timeout=DEFAULT_HTTP_TIMEOUT) as resp:
            if resp.status_code == requests.codes.ok:
                return resp.content
    except Exception as exc:
        logger.warning(f"Failed to download cover for book #{book.book_id}: {exc}")

    return None
