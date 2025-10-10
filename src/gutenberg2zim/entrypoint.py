import logging
from pathlib import Path

from docopt import docopt
from schedule import run_all, run_pending
from zimscraperlib.inputs import compute_descriptions

from gutenberg2zim import i18n
from gutenberg2zim.constants import TMP_FOLDER_PATH, VERSION, logger
from gutenberg2zim.csv_catalog import (
    download_csv_file,
    filter_books,
    get_csv_fpath,
    load_catalog,
)
from gutenberg2zim.rdf import download_rdf_file, get_rdf_fpath, parse_and_fill
from gutenberg2zim.scraper_progress import ScraperProgress
from gutenberg2zim.utils import ALL_FORMATS
from gutenberg2zim.zim import build_zimfile, existing_and_sorted_languages

help_info = (
    """Usage: gutenberg2zim [-F] [-l LANGS] [-f FORMATS] """
    """[-d CACHE_PATH] [-e STATIC_PATH] """
    """[-z ZIM_PATH] [-b BOOKS] """
    """[-t ZIM_TITLE] [-n ZIM_DESC] [-L ZIM_LONG_DESC] """
    """[-c CONCURRENCY] [--no-index] """
    """[--title-search] [--bookshelves] """
    """[--stats-filename STATS_FILENAME] [--publisher ZIM_PUBLISHER] """
    """[--mirror-url MIRROR_URL] [--debug] """
    """

-h --help                       Display this help message
-F --force                      Redo step even if target already exist

-l --languages=<list>           Comma-separated list of lang codes to filter"""
    """ export to (preferably ISO 639-1, else ISO 639-3)
-f --formats=<list>             Comma-separated list of formats to filter """
    """export to (epub, html, pdf, all)

-e --static-folder=<folder>     Use-as/Write-to this folder static HTML
-z --zim-file=<file>            Write ZIM into this file path
-t --zim-title=<title>          Set ZIM title
-n --zim-desc=<description>         Set ZIM description
-L --zim-long-desc=<description>   Set ZIM long description

-d --dl-folder=<folder>         Folder to use/write-to downloaded ebooks
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

    if debug:
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    # create tmp dir
    TMP_FOLDER_PATH.mkdir(parents=True, exist_ok=True)

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

    books: list[int] = []
    try:
        books_csv = books_csv.split(",")

        def f(x):
            return list(map(int, [i for i in x.split("-") if i.isdigit()]))

        for i in books_csv:
            blst = f(i)
            if len(blst) > 1:
                blst = list(range(blst[0], blst[1] + 1))
            books.extend(blst)
        books_csv = list(set(books))
    except Exception as e:
        logger.error(e)
        books_csv = []

    rdf_path = get_rdf_fpath()
    csv_path = get_csv_fpath()

    progress = ScraperProgress(stats_filename)

    # Download CSV catalog
    csv_url = f"{mirror_url}/cache/epub/feeds/pg_catalog.csv.gz"
    logger.info(f"PREPARING CSV catalog from {csv_url}")
    download_csv_file(csv_path=csv_path, csv_url=csv_url)

    # Download RDF files
    rdf_url = f"{mirror_url}/cache/epub/feeds/rdf-files.tar.bz2"
    logger.info(f"PREPARING rdf-files cache from {rdf_url}")
    download_rdf_file(rdf_url=rdf_url, rdf_path=rdf_path)

    # Load catalog and filter books
    logger.info(f"LOADING catalog from {csv_path}")
    catalog = load_catalog(csv_path)

    # Filter books based on languages and specific book IDs
    filtered_books = filter_books(
        catalog=catalog,
        languages=languages if languages else None,
        only_books=books if books else None,
    )

    # Parse only the filtered books from RDF
    logger.info(f"PARSING {len(filtered_books)} filtered books from {rdf_path}")
    parse_and_fill(rdf_path=rdf_path, only_books=filtered_books, progress=progress)
    run_pending()

    # Download ebooks
    # logger.info("DOWNLOADING ebooks from mirror using filters")
    # download_all_books(
    #     mirror_url=mirror_url,
    #     concurrency=dl_concurrency,
    #     formats=formats,
    #     force=force,
    #     progress=progress,
    # )
    # run_pending()
    # logger.info("Finished downloading all books.")

    # Build ZIM file
    logger.info("BUILDING ZIM dynamically")

    # Filter and sort requested languages
    sorted_languages = existing_and_sorted_languages(languages, books)

    build_zimfile(
        output_folder=Path(".").resolve(),
        mirror_url=mirror_url,
        concurrency=concurrency,
        languages=sorted_languages,
        formats=formats,
        only_books=books,
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
