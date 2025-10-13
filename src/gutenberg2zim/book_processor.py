from functools import partial
from http import HTTPStatus
from multiprocessing.dummy import Pool

import apsw
import backoff
import requests

from gutenberg2zim.constants import logger
from gutenberg2zim.download import download_book
from gutenberg2zim.export import export_book, export_skeleton, export_to_json_helpers
from gutenberg2zim.models import repository
from gutenberg2zim.rdf import download_and_parse_book_rdf
from gutenberg2zim.scraper_progress import ScraperProgress

NB_POPULARITY_STARS = 5


def process_all_books(
    book_ids: list[int],
    project_id: str,
    mirror_url: str,
    concurrency: int,
    languages: list[str],
    formats: list[str],
    progress: ScraperProgress,
    *,
    title_search: bool,
    add_lcc_shelves: bool,
) -> None:
    """Download and export all books directly to ZIM without filesystem cache"""

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

    def process_book(book_id: int, progress: ScraperProgress):
        process_book_inner(book_id)
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

        book = download_and_parse_book_rdf(book_id, mirror_url)
        if not book:
            return

        book_content = download_book(
            mirror_url=mirror_url,
            book=book,
            formats=formats,
        )

        if book_content:
            export_book(
                book=book,
                book_files=book_content.files,
                cover_image=book_content.cover_image,
                formats=formats,
                project_id=project_id,
                title_search=title_search,
                add_lcc_shelves=add_lcc_shelves,
            )

    Pool(concurrency).map(partial(process_book, progress=progress), book_ids)

    # Compute popularity (a bit too late for rendering on books pages,
    # but still useful for sorting)
    logger.info("Computing book popularity")
    all_books = repository.get_all_books()
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

    # export to JSON helpers
    logger.info("Exporting JSON helpers")
    export_to_json_helpers(
        languages=languages,
        formats=formats,
        project_id=project_id,
        add_lcc_shelves=add_lcc_shelves,
    )

    # export HTML index and other static files
    logger.info("Exporting HTML skeleton")
    export_skeleton(
        project_id=project_id,
        title_search=title_search,
        add_lcc_shelves=add_lcc_shelves,
    )
