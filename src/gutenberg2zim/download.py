import shutil
import tempfile
import zipfile
from functools import partial
from http import HTTPStatus
from multiprocessing.dummy import Pool
from pathlib import Path

import apsw
import backoff
import requests

from gutenberg2zim.constants import (
    DEFAULT_HTTP_TIMEOUT,
    DL_CHUNCK_SIZE,
    TMP_FOLDER_PATH,
    logger,
)
from gutenberg2zim.database import Book
from gutenberg2zim.export import fname_for, get_list_of_filtered_books
from gutenberg2zim.pg_archive_urls import url_for_type
from gutenberg2zim.scraper_progress import ScraperProgress
from gutenberg2zim.utils import (
    ALL_FORMATS,
    download_file,
    ensure_unicode,
)

# map of preferred document type for every format
PG_PREFERRED_TYPES = {
    "html": ["zip", "html.images", "html.noimages"],
    "epub": ["epub3.images", "epub.images", "epub.noimages"],
    "pdf": ["pdf.images", "pdf.noimages"],
}


def resource_exists(url):
    try:
        r = requests.get(url, stream=True, timeout=DEFAULT_HTTP_TIMEOUT)  # in seconds
        return r.status_code == requests.codes.ok
    except Exception as exc:
        logger.error(f"Exception occurred while testing {url}\n {exc}")
        return False


def handle_zipped_html(zippath: Path, book: Book, dst_dir: Path) -> bool:
    def clfn(fn):
        return Path(fn).name

    def is_safe(fname):
        name = ensure_unicode(clfn(fname))
        if Path(fname).name == name:
            return True
        return fname == f"images/{Path(fname).name}"

    zipped_files = []
    # create temp directory to extract to
    tmpd = tempfile.mkdtemp(dir=TMP_FOLDER_PATH)
    try:
        with zipfile.ZipFile(zippath, "r") as zf:
            # check that there is no insecure data (absolute names)
            if sum([1 for n in zf.namelist() if not is_safe(ensure_unicode(n))]):
                shutil.rmtree(tmpd, ignore_errors=True)
                return False
            # zipped_files = [clfn(fn) for fn in zf.namelist()]
            zipped_files = zf.namelist()

            # extract files from zip
            zf.extractall(tmpd)
    except zipfile.BadZipfile:
        # file is not a zip file when it should be.
        # don't process it anymore as we don't know what to do.
        # could this be due to an incorrect/incomplete download?
        return False

    # is there multiple HTML files in ZIP ? (rare)
    mhtml = (
        sum([1 for f in zipped_files if f.endswith("html") or f.endswith(".htm")]) > 1
    )
    # move all extracted files to proper locations
    for zipped_file in zipped_files:
        src = Path(tmpd) / zipped_file

        # skip folders
        if not Path(src).is_file():
            continue

        # skip cover images
        if "cover" in zipped_file:
            continue

        if src.exists():
            fname = Path(zipped_file).name

            if fname.endswith(".html") or fname.endswith(".htm"):
                if mhtml:
                    if fname.startswith(f"{book.book_id}-h."):
                        dst = dst_dir / f"{book.book_id}.html"
                    else:
                        dst = dst_dir / f"{book.book_id}_{fname}"
                else:
                    dst = dst_dir / f"{book.book_id}.html"
            else:
                dst = dst_dir / f"{book.book_id}_{fname}"
            dst = dst.resolve()
            try:
                logger.debug(f"Moving from {src} to {dst}")
                src.rename(dst)
            except Exception:
                logger.error(f"Failed to move extracted file: {src} -> {dst}")
                raise

    # delete temp directory and zipfile
    zippath.unlink(missing_ok=True)
    shutil.rmtree(tmpd, ignore_errors=True)
    return True


def download_book(
    mirror_url: str,
    book: Book,
    download_cache: Path,
    formats: list[str],
    *,
    force: bool,
):
    logger.info(f"\tDownloading content files for Book #{book.book_id}")

    # apply filters
    if not formats:
        formats = ALL_FORMATS

    # HTML is our base for ZIM for add it if not present
    if "html" not in formats:
        formats.append("html")

    book_dir = download_cache / str(book.book_id)

    if force:
        shutil.rmtree(book_dir)

    book_dir.mkdir(parents=True, exist_ok=True)

    unsupported_formats = []
    for book_format in formats:
        logger.debug(f"Processing {book_format}")

        # if we already know (e.g. due to a former pass) that this book format is not
        # supported, no need to retry
        if book.unsupported_formats and book_format in book.unsupported_formats:
            logger.debug(f"\t\tNo file available for {book_format} of #{book.book_id}")
            continue

        fpath = book_dir / fname_for(book, book_format)

        # check if already downloaded
        if fpath.exists() and not force:
            logger.debug(
                f"\t\t{book_format} already exists for book #{book.book_id}, "
                "reusing existing file"
            )
            continue

        pg_type_to_use = None
        pg_resp = None
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

            pg_resp = requests.get(
                url, stream=True, timeout=DEFAULT_HTTP_TIMEOUT
            )  # in seconds

            if pg_resp.status_code == requests.codes.ok:
                pg_type_to_use = pg_type
                break

            pg_resp.close()

        if not url or not pg_type_to_use:
            logger.debug(f"\t\tNo file available for {book_format} of #{book.book_id}")
            unsupported_formats.append(book_format)
            continue

        if not pg_resp:
            # not supposed to happen, this is a bug
            raise Exception(
                f"Missing streamed response for {book_format} of #{book.book_id}"
            )

        if url.endswith(".zip"):
            zpath = book_dir / f"{fname_for(book, book_format)}.zip"
            with open(zpath, "wb") as fh:
                for chunk in pg_resp.iter_content(chunk_size=DL_CHUNCK_SIZE):
                    if chunk:
                        fh.write(chunk)
            # extract zipfile
            handle_zipped_html(
                zippath=zpath,
                book=book,
                dst_dir=book_dir,
            )
        else:
            with open(fpath, "wb") as fh:
                for chunk in pg_resp.iter_content(chunk_size=DL_CHUNCK_SIZE):
                    if chunk:
                        fh.write(chunk)

    # update list of unsupported formats based on the union of format already known to
    # not be supported and new ones
    book.unsupported_formats = ",".join(  # type: ignore
        set(
            unsupported_formats
            + (
                str(book.unsupported_formats).split(",")
                if book.unsupported_formats
                else []
            )
        )
    )
    book.save()

    # delete book from DB if not downloaded in any format
    if len(unsupported_formats) == len(formats):
        logger.warning(
            f"\t\tBook #{book.book_id} could not be downloaded in any format. "
            "Deleting from DB ..."
        )
        book.delete_instance()
        if book_dir.exists():
            shutil.rmtree(book_dir, ignore_errors=True)
        return
    download_cover(mirror_url, book, book_dir)


def download_cover(mirror_url, book, book_dir):
    has_cover = Book.select(Book.cover_page).where(Book.book_id == book.book_id)
    if has_cover:
        url = (
            f"{mirror_url}/cache/epub/{book.book_id}/pg{book.book_id}.cover.medium.jpg"
        )
        cover = f"{book.book_id}_cover_image.jpg"
        if (book_dir / cover).exists():
            logger.debug(f"Cover already exists for book #{book.book_id}")
            return

        logger.debug(f"Downloading {url}")
        download_file(url, book_dir / cover)
    else:
        logger.debug(f"No Book Cover found for Book #{book.book_id}")


def download_all_books(
    mirror_url: str,
    download_cache: Path,
    concurrency: int,
    languages: list[str],
    formats: list[str],
    only_books: list[int],
    *,
    force: bool,
    progress: ScraperProgress,
):
    available_books = get_list_of_filtered_books(
        languages=languages, formats=formats, only_books=only_books
    )
    progress.increase_total(len(available_books))

    # ensure dir exist
    download_cache.mkdir(parents=True, exist_ok=True)

    def backoff_busy_error_hdlr(details):
        logger.warning(
            "Backing off {wait:0.1f} seconds after {tries} tries "
            "calling function {target} with args {args} and kwargs "
            "{kwargs} due to apsw.BusyError".format(**details)
        )

    def backoff_request_error_hdlr(details):
        logger.warning(
            "Backing off {wait:0.1f} seconds after {tries} tries "
            "calling function {target} with args {args} and kwargs "
            "{kwargs} due to requests error".format(**details)
        )

    def fatal_code(e):
        """Give up on errors codes 400-499 except 429"""
        if isinstance(e, requests.HTTPError) and (
            HTTPStatus.BAD_REQUEST
            <= e.response.status_code
            < HTTPStatus.INTERNAL_SERVER_ERROR
            and e.response.status_code != HTTPStatus.TOO_MANY_REQUESTS
        ):
            logger.warning(
                f"{e.request.url} returned a non-retryable HTTP error code "
                f"{e.response.status_code}"
            )
            return True
        return False

    def dlb(b, progress: ScraperProgress):
        dlb_inner(b)
        progress.increase_progress()

    @backoff.on_exception(
        partial(backoff.expo, base=3, factor=2),
        requests.exceptions.RequestException,
        max_time=30,  # secs
        on_backoff=backoff_request_error_hdlr,
        giveup=fatal_code,
    )
    @backoff.on_exception(
        backoff.constant,
        apsw.BusyError,
        max_time=3,
        on_backoff=backoff_busy_error_hdlr,
    )
    def dlb_inner(b):
        return download_book(
            mirror_url=mirror_url,
            book=b,
            download_cache=download_cache,
            formats=formats,
            force=force,
        )

    Pool(concurrency).map(partial(dlb, progress=progress), available_books)
