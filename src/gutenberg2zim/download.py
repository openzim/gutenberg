import shutil
import tempfile
import zipfile
from multiprocessing.dummy import Pool
from pathlib import Path

import apsw
import backoff
import requests
from kiwixstorage import KiwixStorage

from gutenberg2zim.constants import TMP_FOLDER_PATH, logger
from gutenberg2zim.database import Book
from gutenberg2zim.export import fname_for, get_list_of_filtered_books
from gutenberg2zim.pg_archive_urls import url_for_type
from gutenberg2zim.s3 import download_from_cache
from gutenberg2zim.utils import (
    ALL_FORMATS,
    archive_name_for,
    download_file,
    ensure_unicode,
    get_etag_from_url,
)

# map of preferred document type for every format
PG_PREFERRED_TYPES = {
    "html": ["zip", "html.images", "html.noimages"],
    "epub": ["epub3.images", "epub.images", "epub.noimages"],
    "pdf": ["pdf.images", "pdf.noimages"],
}

IMAGE_BASE = "http://aleph.pglaf.org/cache/epub/"

DL_CHUNCK_SIZE = 8192


def resource_exists(url):
    try:
        r = requests.get(url, stream=True, timeout=20)  # in seconds
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
    book: Book,
    download_cache: Path,
    formats: list[str],
    *,
    force: bool,
    s3_storage: KiwixStorage | None,
    optimizer_version: dict[str, str] | None,
):
    logger.info(f"\tDownloading content files for Book #{book.book_id}")

    # apply filters
    if not formats:
        formats = ALL_FORMATS

    # HTML is our base for ZIM for add it if not present
    if "html" not in formats:
        formats.append("html")

    book_dir = download_cache / str(book.book_id)
    optimized_dir = book_dir / "optimized"
    unoptimized_dir = book_dir / "unoptimized"

    if force:
        shutil.rmtree(book_dir)

    unoptimized_dir.mkdir(parents=True, exist_ok=True)
    optimized_dir.mkdir(parents=True, exist_ok=True)

    unsupported_formats = []
    for book_format in formats:
        logger.debug(f"Processing {book_format}")

        # if we already know (e.g. due to a former pass) that this book format is not
        # supported, no need to retry
        if book.unsupported_formats and book_format in book.unsupported_formats:
            logger.debug(f"\t\tNo file available for {book_format} of #{book.book_id}")
            continue

        unoptimized_fpath = unoptimized_dir / fname_for(book, book_format)
        optimized_fpath = optimized_dir / archive_name_for(book, book_format)

        # check if already downloaded
        if (unoptimized_fpath.exists() or optimized_fpath.exists()) and not force:
            logger.debug(
                f"\t\t{book_format} already exists for book #{book.book_id}, "
                "reusing existing file"
            )
            continue

        pg_type_to_use = None
        pg_resp = None
        url = None
        for pg_type in PG_PREFERRED_TYPES[book_format]:
            url = url_for_type(pg_type, book.book_id)
            if not url:
                # not supposed to happen, this is a bug
                raise Exception(
                    f"Unsupported {pg_type} pg_type for {book_format} #{book.book_id}"
                )

            pg_resp = requests.get(url, stream=True, timeout=20)  # in seconds

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

        etag = pg_resp.headers.get("Etag", None)

        if s3_storage and download_from_cache(
            book=book,
            etag=etag,
            book_format=book_format,
            dest_dir=optimized_dir,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version,
        ):
            # explicitely close the response since we will not consume the stream
            pg_resp.close()
        elif url.endswith(".zip"):
            zpath = unoptimized_dir / f"{fname_for(book, book_format)}.zip"
            with open(zpath, "wb") as fh:
                for chunk in pg_resp.iter_content(chunk_size=DL_CHUNCK_SIZE):
                    if chunk:
                        fh.write(chunk)
            # extract zipfile
            handle_zipped_html(
                zippath=zpath,
                book=book,
                dst_dir=unoptimized_dir,
            )
        else:
            with open(unoptimized_fpath, "wb") as fh:
                for chunk in pg_resp.iter_content(chunk_size=DL_CHUNCK_SIZE):
                    if chunk:
                        fh.write(chunk)

        # save etag for optimized formats
        if book_format == "html":
            book.html_etag = etag  # type: ignore
        elif book_format == "epub":
            book.epub_etag = etag  # type: ignore

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
    download_cover(book, book_dir, s3_storage, optimizer_version)


def download_cover(book, book_dir, s3_storage, optimizer_version):
    has_cover = Book.select(Book.cover_page).where(Book.book_id == book.book_id)
    if has_cover:
        # try to download optimized cover from cache if s3_storage
        url = f"{IMAGE_BASE}{book.book_id}/pg{book.book_id}.cover.medium.jpg"
        etag = get_etag_from_url(url)
        downloaded_from_cache = False
        cover = f"{book.book_id}_cover_image.jpg"
        if (book_dir / "optimized" / cover).exists() or (
            book_dir / "unoptimized" / cover
        ).exists():
            logger.debug(f"Cover already exists for book #{book.book_id}")
            return
        if s3_storage:
            logger.info(
                f"Trying to download cover for {book.book_id} from optimization cache"
            )
            downloaded_from_cache = download_from_cache(
                book=book,
                etag=etag,
                book_format="cover",
                dest_dir=book_dir / "optimized",
                s3_storage=s3_storage,
                optimizer_version=optimizer_version,
            )
        if not downloaded_from_cache:
            logger.debug(f"Downloading {url}")
            if download_file(url, book_dir / "unoptimized" / cover):
                book.cover_etag = etag
                book.save()
    else:
        logger.debug(f"No Book Cover found for Book #{book.book_id}")


def download_all_books(
    download_cache: Path,
    concurrency: int,
    languages: list[str],
    formats: list[str],
    only_books: list[int],
    *,
    force: bool,
    s3_storage: KiwixStorage | None,
    optimizer_version: dict[str, str] | None,
):
    available_books = get_list_of_filtered_books(
        languages=languages, formats=formats, only_books=only_books
    )

    # ensure dir exist
    download_cache.mkdir(parents=True, exist_ok=True)

    def backoff_busy_error_hdlr(details):
        logger.warning(
            "Backing off {wait:0.1f} seconds after {tries} tries "
            "calling function {target} with args {args} and kwargs "
            "{kwargs} due to apsw.BusyError".format(**details)
        )

    @backoff.on_exception(
        backoff.constant,
        apsw.BusyError,
        max_time=3,
        on_backoff=backoff_busy_error_hdlr,
    )
    def dlb(b):
        return download_book(
            book=b,
            download_cache=download_cache,
            formats=formats,
            force=force,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version,
        )

    Pool(concurrency).map(dlb, available_books)
