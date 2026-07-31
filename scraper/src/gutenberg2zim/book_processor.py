from functools import partial
from http import HTTPStatus
from multiprocessing.dummy import Pool

import apsw
import backoff
import requests

from gutenberg2zim.adapters import book_to_work, work_to_book
from gutenberg2zim.constants import logger
from gutenberg2zim.core.ports import MetadataPort, WorkRef
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler
from gutenberg2zim.download import download_book
from gutenberg2zim.export import (
    export_book,
    export_infobox_assets,
    generate_json_files,
    generate_noscript_pages,
)
from gutenberg2zim.models import Book
from gutenberg2zim.scraper_progress import ScraperProgress
from gutenberg2zim.sources.gutenberg.catalog import GUTENBERG_SOURCE
from gutenberg2zim.sources.gutenberg.metadata import GutenbergRdfMetadata

NB_POPULARITY_STARS = 3


class GutenbergProcessor:
    """Per-book pipeline for the Gutenberg source, wired through ports.

    Metadata goes through the `MetadataPort`; format resolution happens via
    the `FormatResolverPort` inside `download_book`; HTML rewriting still
    calls `update_html_for_static` directly (see `GutenbergHtmlRewriter`'s
    docstring for why the port is not used there yet).
    """

    def __init__(
        self,
        *,
        metadata: MetadataPort,
        mirror_url: str,
        formats: list[str],
        zim_name: str,
        work_store: WorkStore,
        assembler: ZimAssembler,
        title_search: bool,
        add_lcc_shelves: bool,
    ):
        self.metadata = metadata
        self.mirror_url = mirror_url
        self.formats = formats
        self.zim_name = zim_name
        self.work_store = work_store
        self.assembler = assembler
        self.title_search = title_search
        self.add_lcc_shelves = add_lcc_shelves

    def fetch_book(self, book_id: int) -> Book | None:
        """Fetch metadata for one book via the metadata port and store it"""
        works = list(
            self.metadata.fetch([WorkRef(id=str(book_id), source=GUTENBERG_SOURCE)])
        )
        if not works:
            return None
        self.work_store.add(works[0])
        return work_to_book(works[0])

    def process(self, book_id: int):
        """Download book content and export directly to ZIM"""
        book = self.fetch_book(book_id)
        if not book:
            return

        book_content = download_book(
            mirror_url=self.mirror_url,
            book=book,
            formats=self.formats,
            work_store=self.work_store,
        )

        if book_content:
            export_book(
                book=book,
                book_files=book_content.files,
                formats=self.formats,
                mirror_url=self.mirror_url,
                assembler=self.assembler,
                _zim_name=self.zim_name,
                _title_search=self.title_search,
                _add_lcc_shelves=self.add_lcc_shelves,
            )


def process_all_books(
    book_ids: list[int],
    zim_name: str,
    mirror_url: str,
    concurrency: int,
    _languages: list[str],
    formats: list[str],
    progress: ScraperProgress,
    work_store: WorkStore,
    assembler: ZimAssembler,
    *,
    title_search: bool,
    add_lcc_shelves: bool,
    title: str | None = None,
    description: str | None = None,
    primary_color: str | None = None,
    secondary_color: str | None = None,
) -> None:
    """Download and export all books directly to ZIM without filesystem cache"""

    # Export infobox assets (CSS, JS, and icons) first to fail fast if there's an issue
    logger.info("Exporting infobox assets")
    export_infobox_assets(assembler)

    logger.info(
        f"Processing {len(book_ids)} books with {concurrency} (parallel) worker(s)"
    )

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

    processor = GutenbergProcessor(
        metadata=GutenbergRdfMetadata(mirror_url),
        mirror_url=mirror_url,
        formats=formats,
        zim_name=zim_name,
        work_store=work_store,
        assembler=assembler,
        title_search=title_search,
        add_lcc_shelves=add_lcc_shelves,
    )

    def process_book(book_id: int, progress: ScraperProgress):
        try:
            process_book_inner(book_id)
        except Exception:
            logger.error(
                f"Fatal error received with processing book {book_id}", exc_info=True
            )
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
    def process_book_inner(book_id: int):
        """Download book content and export directly to ZIM with retry logic"""
        processor.process(book_id)

    Pool(concurrency).map(partial(process_book, progress=progress), book_ids)

    # Compute popularity (a bit too late for rendering on books pages,
    # but still useful for sorting)
    logger.info("Computing book popularity")
    all_books = sorted(
        (work_to_book(work) for work in work_store.works),
        key=lambda book: book.downloads,
        reverse=True,
    )

    # Check if any books were successfully downloaded
    if not all_books:
        logger.error("No books were successfully processed")
        raise RuntimeError(
            "All books failed to process. Cannot create ZIM without any content."
        )

    all_books_count = len(all_books)
    stars_limits = [0] * NB_POPULARITY_STARS
    stars = NB_POPULARITY_STARS
    nb_downloads = all_books[0].downloads
    for ibook in range(0, len(all_books), 1):
        if (
            ibook
            > float(NB_POPULARITY_STARS - stars + 1)
            / NB_POPULARITY_STARS
            * all_books_count
            and all_books[ibook].downloads < nb_downloads
        ):
            stars_limits[stars - 1] = nb_downloads
            stars = stars - 1
        nb_downloads = all_books[ibook].downloads

    for book in all_books:
        book.popularity = sum(
            [int(book.downloads >= stars_limits[i]) for i in range(NB_POPULARITY_STARS)]
        )
        # Write the computed popularity back into the store
        work_store.add(book_to_work(book))

    # export to JSON files (new format for Vue.js UI)
    logger.info("Generating JSON files for Vue.js UI")
    generate_json_files(
        zim_name=zim_name,
        formats=formats,
        work_store=work_store,
        assembler=assembler,
        title=title,
        description=description,
        add_lcc_shelves=add_lcc_shelves,
        primary_color=primary_color,
        secondary_color=secondary_color,
    )

    # Generate No-JS fallback pages
    logger.info("Generating No-JS fallback pages")
    generate_noscript_pages(
        formats=formats,
        work_store=work_store,
        assembler=assembler,
    )
