import logging
import os
from pathlib import Path

from docopt import docopt
from schedule import run_all
from zimscraperlib.inputs import compute_descriptions

from gutenberg2zim import i18n
from gutenberg2zim.constants import VERSION, logger
from gutenberg2zim.csv_catalog import (
    download_csv_file,
    filter_books,
    get_csv_fpath,
    load_catalog,
)
from gutenberg2zim.scraper_progress import ScraperProgress
from gutenberg2zim.utils import ALL_FORMATS, critical_error
from gutenberg2zim.zim import build_zimfile

help_info = (
    """Usage: gutenberg2zim [-F] [-l LANGS] [-f FORMATS] """
    """[-d CACHE_PATH] [-e STATIC_PATH] """
    """[-z ZIM_PATH] [-b BOOKS] """
    """[-t ZIM_TITLE] [-n ZIM_DESC] [-L ZIM_LONG_DESC] """
    """[-c CONCURRENCY] [--no-index] """
    """[--title-search] [--bookshelves] """
    """[--stats-filename STATS_FILENAME] [--publisher ZIM_PUBLISHER] """
    """[--mirror-url MIRROR_URL] [--output OUTPUT_FOLDER][--debug] """
    """

-h --help                       Display this help message
-F --force                      Redo step even if target already exist

-l --languages=<list>           Comma-separated list of lang codes to filter"""
    """ export to (preferably ISO 639-1, else ISO 639-3)
-f --formats=<list>             Comma-separated list of formats to filter """
    """export to (epub, html, pdf, all)

-z --zim-file=<file>            Write ZIM into this file path
-t --zim-title=<title>          Set ZIM title
-n --zim-desc=<description>         Set ZIM description
-L --zim-long-desc=<description>   Set ZIM long description

-b --books=<ids>                Execute the processes for specific books, """
    """separated by commas, or dashes for intervals
-c --concurrency=<nb>           Number of concurrent process for processing """
    """tasks
--no-index                      Do NOT create full-text index within ZIM file
--title-search                  Add field to search a book by title and directly """
    """jump to it
--bookshelves                   Add bookshelves
--stats-filename=<filename>  Path to store the progress JSON file to
--publisher=<zim_publisher>     Custom Publisher in ZIM Metadata (openZIM otherwise)
--mirror_url=<mirror_url>       Optional custom url of mirror hosting Gutenberg files
--output=<output_folder>        Output folder for ZIMs. Default: ./output
--debug                         Enable verbose output

This script is used to produce a ZIM file of Gutenberg repository using a mirror.
The scraper will download the catalog and RDF files, parse metadata, download books,
and create the ZIM file."""
)


def main():
    arguments = docopt(help_info, version=VERSION)

    zim_name = arguments.get("--zim-file")
    mirror_url = arguments.get("--mirror-url") or "https://gutenberg.mirror.driftle.ss"

    books_csv = arguments.get("--books") or ""
    zim_title = arguments.get("--zim-title")

    zim_desc = arguments.get("--zim-desc")
    zim_long_description = arguments.get("--zim-long-desc")

    concurrency = int(arguments.get("--concurrency") or 16)
    force = arguments.get("--force", False)
    title_search = arguments.get("--title-search", False)
    bookshelves = arguments.get("--bookshelves", False)
    stats_filename: str | None = arguments.get("--stats-filename") or None
    publisher = arguments.get("--publisher") or "openZIM"
    debug = arguments.get("--debug") or False
    output_folder = Path(
        arguments.get("--output") or os.getenv("GUTENBERG_OUTPUT", "./output")
    )

    if debug:
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    i18n.setup_i18n()

    languages = [
        x.strip().lower()
        for x in (arguments.get("--languages") or "").split(",")
        if x.strip()
    ]
    # special shortcuts for "all"
    formats: list[str]
    if arguments.get("--formats") in ["all", None]:
        formats = ALL_FORMATS
    else:
        formats = list(
            {
                x.strip().lower()
                for x in (arguments.get("--formats") or "").split(",")
                if x.strip()
            }
        )

    description, long_description = compute_descriptions(
        "",
        zim_desc,
        zim_long_description,
    )

    only_books_ids: list[int] = []
    books_csv = books_csv.split(",")
    for books_value in books_csv:
        blst = list(map(int, [i for i in books_value.split("-") if i.isdigit()]))
        if len(blst) > 1:
            blst = list(range(blst[0], blst[1] + 1))
        only_books_ids.extend(blst)
    only_books_ids = list(set(only_books_ids))

    csv_path = get_csv_fpath()

    progress = ScraperProgress(stats_filename)
    progress.increase_total(1)

    # Download CSV catalog
    csv_url = f"{mirror_url}/cache/epub/feeds/pg_catalog.csv.gz"
    logger.info(f"PREPARING CSV catalog from {csv_url}")
    download_csv_file(csv_path=csv_path, csv_url=csv_url)

    # Load catalog and filter books
    logger.info(f"LOADING catalog from {csv_path}")
    catalog = load_catalog(csv_path)

    # Filter books based on languages and specific book IDs
    book_ids = filter_books(
        catalog=catalog,
        languages=languages if languages else None,
        only_books=only_books_ids if only_books_ids else None,
    )
    if not len(book_ids):
        critical_error(
            "Unable to proceed. Combination of languages, "
            "books and formats has no result."
        )
    book_languages = (
        languages
        if languages
        else list({languages for book_id in book_ids for languages in catalog[book_id]})
    )
    progress.increase_progress()

    # Build ZIM file
    logger.info("BUILDING ZIM")

    build_zimfile(
        output_folder=output_folder,
        book_ids=book_ids,
        mirror_url=mirror_url,
        concurrency=concurrency,
        languages=book_languages,
        formats=formats,
        is_selection=len(only_books_ids) > 0,
        zim_name=Path(zim_name).name if zim_name else None,
        title=zim_title,
        description=description,
        long_description=long_description,
        publisher=publisher,
        force=force,
        title_search=title_search,
        add_bookshelves=bookshelves,
        progress=progress,
    )

    # Final increase to indicate we are done
    progress.increase_progress()
    run_all()  # force flushing scraper progress to file

    logger.info("Scraper has finished normally")
