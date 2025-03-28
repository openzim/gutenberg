import shutil
import tempfile
import zipfile
from multiprocessing.dummy import Pool
from pathlib import Path
from pprint import pformat

import apsw
import backoff
from kiwixstorage import KiwixStorage

from gutenberg2zim.constants import TMP_FOLDER_PATH, logger
from gutenberg2zim.database import Book, BookFormat
from gutenberg2zim.export import fname_for, get_list_of_filtered_books
from gutenberg2zim.s3 import download_from_cache
from gutenberg2zim.urls import get_urls
from gutenberg2zim.utils import (
    FORMAT_MATRIX,
    archive_name_for,
    download_file,
    ensure_unicode,
    get_etag_from_url,
)

IMAGE_BASE = "http://aleph.pglaf.org/cache/epub/"

# for development
# def resource_exists(url):
#     try:
#         r = requests.get(url, stream=True, timeout=20)  # in seconds
#         return r.status_code == requests.codes.ok
#     except Exception as exc:
#         logger.error(f"Exception occurred while testing {url}\n {exc}")
#         return False


def handle_zipped_epub(zippath: Path, book: Book, dst_dir: Path) -> bool:
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
        # skip folders
        if not Path(zipped_file).is_file():
            continue

        src = Path(tmpd) / zipped_file
        if src.exists():
            fname = Path(zipped_file).name

            if fname.endswith(".html") or fname.endswith(".htm"):
                if mhtml:
                    if fname.startswith(f"{book.id}-h."):
                        dst = dst_dir / f"{book.id}.html"
                    else:
                        dst = dst_dir / f"{book.id}_{fname}"
                else:
                    dst = dst_dir / f"{book.id}.html"
            else:
                dst = dst_dir / f"{book.id}_{fname}"
            dst = dst.resolve()
            try:
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
    logger.info(f"\tDownloading content files for Book #{book.id}")

    # apply filters
    if not formats:
        formats = list(FORMAT_MATRIX.keys())

    # HTML is our base for ZIM for add it if not present
    if "html" not in formats:
        formats.append("html")

    book_dir = download_cache / str(book.id)
    optimized_dir = book_dir / "optimized"
    unoptimized_dir = book_dir / "unoptimized"

    unsuccessful_formats = []
    for book_format in formats:
        unoptimized_fpath = unoptimized_dir / fname_for(book, book_format)
        unoptimized_fpath = unoptimized_dir / fname_for(book, book_format)
        optimized_fpath = optimized_dir / archive_name_for(book, book_format)

        # check if already downloaded
        if (unoptimized_fpath.exists() or optimized_fpath.exists()) and not force:
            logger.debug(f"\t\t{book_format} already exists for book #{book.id}")
            continue

        if force:
            if book_format == "html":
                for fpath in book_dir.iterdir():
                    if fpath.is_file() and fpath.suffix not in [".pdf", ".epub"]:
                        fpath.unlink(missing_ok=True)
            else:
                unoptimized_fpath.unlink(missing_ok=True)
                optimized_fpath.unlink(missing_ok=True)
            # delete dirs which are empty
            for dir_name in [optimized_dir, unoptimized_dir]:
                if not dir_name.exists():
                    continue
                if not list(dir_name.iterdir()):
                    dir_name.rmdir()

        # retrieve corresponding BookFormat
        bfs = BookFormat.filter(book=book)

        if book_format == "html":
            patterns = [
                "mnsrb10h.htm",
                "8ledo10h.htm",
                "tycho10f.htm",
                "8ledo10h.zip",
                "salme10h.htm",
                "8nszr10h.htm",
                "{id}-h.html",
                "{id}.html.gen",
                "{id}-h.htm",
                "8regr10h.zip",
                "{id}.html.noimages",
                "8lgme10h.htm",
                "tycho10h.htm",
                "tycho10h.zip",
                "8lgme10h.zip",
                "8indn10h.zip",
                "8resp10h.zip",
                "20004-h.htm",
                "8indn10h.htm",
                "8memo10h.zip",
                "fondu10h.zip",
                "{id}-h.zip",
                "8mort10h.zip",
            ]
            bfso = bfs
            bfs = bfs.filter(BookFormat.pattern << patterns)
            if not bfs.count():
                logger.debug(pformat([(bf.mime, bf.images, bf.pattern) for bf in bfs]))
                logger.debug(pformat([(bf.mime, bf.images, bf.pattern) for bf in bfso]))
                logger.error("html not found")
                unsuccessful_formats.append(book_format)
                continue
        else:
            bfs = bfs.filter(mime=FORMAT_MATRIX.get(book_format))  # type: ignore

        if not bfs.count():
            logger.debug(f"[{book_format}] not avail. for #{book.id}# {book.title}")
            unsuccessful_formats.append(book_format)
            continue

        if bfs.count() > 1:
            try:
                bf = bfs.filter(bfs.images).get()
            except Exception:
                bf = bfs.get()
        else:
            bf = bfs.get()

        logger.debug(f"[{book_format}] Requesting URLs for #{book.id}# {book.title}")

        # retrieve list of URLs for format unless we have it in DB
        if bf.downloaded_from and not force:
            urls = [bf.downloaded_from]
        else:
            urld = get_urls(book)
            urls = list(
                reversed(urld.get(FORMAT_MATRIX.get(book_format)))  # type: ignore
            )

        import copy

        allurls = copy.copy(urls)
        downloaded_from_cache = False

        while urls:
            url = urls.pop()

            # for development
            # if len(allurls) != 1:
            #     if not resource_exists(url):
            #         continue

            # HTML files are *sometime* available as ZIP files
            if url.endswith(".zip"):
                zpath = unoptimized_dir / f"{fname_for(book, book_format)}.zip"

                etag = get_etag_from_url(url)
                if s3_storage:
                    if download_from_cache(
                        book=book,
                        etag=etag,
                        book_format=book_format,
                        dest_dir=optimized_dir,
                        s3_storage=s3_storage,
                        optimizer_version=optimizer_version,
                    ):
                        downloaded_from_cache = True
                        break
                if not download_file(url, zpath):
                    logger.error(f"ZIP file download failed: {zpath}")
                    continue
                # save etag
                book.html_etag = etag  # type: ignore
                book.save()
                # extract zipfile
                handle_zipped_epub(
                    zippath=zpath,
                    book=book,
                    dst_dir=unoptimized_dir,
                )
            else:
                if (
                    url.endswith(".htm")
                    or url.endswith(".html")
                    or url.endswith(".html.utf8")
                    or url.endswith(".epub")
                ):
                    etag = get_etag_from_url(url)
                    if s3_storage:
                        logger.info(
                            f"Trying to download {book.id} from optimization cache"
                        )
                        if download_from_cache(
                            book=book,
                            etag=etag,
                            book_format=book_format,
                            dest_dir=optimized_dir,
                            s3_storage=s3_storage,
                            optimizer_version=optimizer_version,
                        ):
                            downloaded_from_cache = True
                            break
                if not download_file(url, unoptimized_fpath):
                    logger.error(f"file donwload failed: {unoptimized_fpath}")
                    continue
                # save etag if html or epub if download is successful
                if (
                    url.endswith(".htm")
                    or url.endswith(".html")
                    or url.endswith(".html.utf8")
                ):
                    logger.debug(f"Saving html ETag for {book.id}")
                    book.html_etag = etag  # type: ignore
                    book.save()
                elif url.endswith(".epub"):
                    logger.debug(f"Saving epub ETag for {book.id}")
                    book.epub_etag = etag  # type: ignore
                    book.save()

            # store working URL in DB
            bf.downloaded_from = url
            bf.save()
            # break as we got a working URL
            break

        if not bf.downloaded_from and not downloaded_from_cache:
            logger.error(
                "No file found for book #%d in format %s", book.id, book_format
            )

            # delete instance from DB if download failed
            logger.info("Deleting instance from DB")
            bf.delete_instance()
            unsuccessful_formats.append(book_format)
            logger.debug("Tried all URLs:\n%s", pformat(allurls))

    # delete book from DB if not downloaded in any format
    if len(unsuccessful_formats) == len(formats):
        logger.debug(
            f"Book #{book.id} could not be downloaded in any format. "
            "Deleting from DB ..."
        )
        book.delete_instance()
        if book_dir.exists():
            shutil.rmtree(book_dir, ignore_errors=True)
        return
    download_cover(book, book_dir, s3_storage, optimizer_version)


def download_cover(book, book_dir, s3_storage, optimizer_version):
    has_cover = Book.select(Book.cover_page).where(Book.id == book.id)
    if has_cover:
        # try to download optimized cover from cache if s3_storage
        url = f"{IMAGE_BASE}{book.id}/pg{book.id}.cover.medium.jpg"
        etag = get_etag_from_url(url)
        downloaded_from_cache = False
        cover = f"{book.id}_cover_image.jpg"
        if (book_dir / "optimized" / cover).exists() or (
            book_dir / "unoptimized" / cover
        ).exists():
            logger.debug(f"Cover already exists for book #{book.id}")
            return
        if s3_storage:
            logger.info(
                f"Trying to download cover for {book.id} from optimization cache"
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
        logger.debug(f"No Book Cover found for Book #{book.id}")


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
