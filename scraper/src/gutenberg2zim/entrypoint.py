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
    """[--zim-languages LANGUAGES] [--zim-name ZIM_NAME] [-c CONCURRENCY]"""
    """[--no-index] [--title-search] [--lcc-shelves SHELVES] """
    """[--stats-filename STATS_FILENAME] [--publisher ZIM_PUBLISHER] """
    """[--mirror-url MIRROR_URL] [--output OUTPUT_FOLDER] """
    """[--ui-dist UI_DIST] [--debug] """
    """

-h --help                       Display this help message
-F --force                      Redo step even if target already exist

-l --languages=<list>           Comma-separated list of lang codes to filter"""
    """ export to (preferably ISO 639-1, else ISO 639-3)
-f --formats=<list>             Comma-separated list of formats to filter """
    """export to (epub, html, pdf, all)

-z --zim-file=<file>            Write ZIM into at this file path
--zim-name=<name>               Set ZIM name (metadata)
-t --zim-title=<title>          Set ZIM title
-n --zim-desc=<description>         Set ZIM description
-L --zim-long-desc=<description>   Set ZIM long description
--zim-languages=<languages>          Set ZIM Language metadata

-b --books=<ids>                Execute the processes for specific books, """
    """separated by commas, or dashes for intervals
-c --concurrency=<nb>           Number of concurrent process for processing """
    """tasks
--no-index                      Do NOT create full-text index within ZIM file
--title-search                  Add field to search a book by title and directly """
    """jump to it
--lcc-shelves=<shelves>         Comma-separated list of LCC shelf codes to include """
    """(e.g., P,PR,Q). Use 'all' to generate all shelves. If omitted, no shelf generated
--stats-filename=<filename>  Path to store the progress JSON file to
--publisher=<zim_publisher>     Custom Publisher in ZIM Metadata (openZIM otherwise)
--mirror_url=<mirror_url>       Optional custom url of mirror hosting Gutenberg files
--output=<output_folder>        Output folder for ZIMs. Default: ./output
--ui-dist=<ui_dist>              Directory containing Vue.js UI build output (ui/dist).
                                 Default: ../ui/dist or GUTENBERG_UI_DIST env var
--debug                         Enable verbose output

This script is used to produce a ZIM file of Gutenberg repository using a mirror.
The scraper will download the catalog and RDF files, parse metadata, download books,
and create the ZIM file."""
)


def main():
    arguments = docopt(help_info, version=VERSION)

    zim_file = arguments.get("--zim-file")
    zim_name = arguments.get("--zim-name")
    mirror_url = arguments.get("--mirror-url") or "https://gutenberg.mirror.driftle.ss"

    books_csv = arguments.get("--books") or ""
    zim_title = arguments.get("--zim-title")

    zim_desc = arguments.get("--zim-desc")
    zim_long_description = arguments.get("--zim-long-desc")

    concurrency = int(arguments.get("--concurrency") or 16)
    force = arguments.get("--force", False)
    title_search = arguments.get("--title-search", False)

    with_fulltext_index = not arguments.get("--no-index", False)

    # Parse --lcc-shelves argument
    # None = not passed (don't filter by shelves, don't generate shelf pages)
    # "all" = generate all shelves
    # "P,PR,Q" = filter and generate only these shelves
    supported_shelves = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "J",
        "K",
        "L",
        "M",
        "N",
        "P",
        "PA",
        "PB",
        "PC",
        "PD",
        "PE",
        "PF",
        "PG",
        "PH",
        "PJ",
        "PK",
        "PL",
        "PM",
        "PN",
        "PQ",
        "PR",
        "PS",
        "PT",
        "PZ",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "Z",
    ]
    lcc_shelves_arg = arguments.get("--lcc-shelves")
    lcc_shelves: list[str] | None = None
    add_lcc_shelves = False
    if lcc_shelves_arg is not None:
        add_lcc_shelves = True
        if lcc_shelves_arg.strip().lower() == "all":
            lcc_shelves = []  # Empty list means all shelves
        else:
            lcc_shelves = [
                s.strip().upper()
                for s in lcc_shelves_arg.split(",")
                if s.strip().upper() in supported_shelves
            ]

    stats_filename: str | None = arguments.get("--stats-filename") or None
    publisher = arguments.get("--publisher") or "openZIM"
    debug = arguments.get("--debug") or False
    output_folder = Path(
        arguments.get("--output") or os.getenv("GUTENBERG_OUTPUT", "./output")
    )
    # Calculate default UI dist path: from scraper/src/gutenberg2zim/entrypoint.py
    # go up to repo root, then to ui/dist
    default_ui_dist = Path(__file__).parent.parent.parent.parent.parent / "ui" / "dist"
    ui_dist = Path(
        arguments.get("--ui-dist")
        or os.getenv("GUTENBERG_UI_DIST", str(default_ui_dist))
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

    # Filter books based on languages, specific book IDs, and LCC shelves
    filtered_books = filter_books(
        catalog=catalog,
        languages=languages if languages else None,
        only_books=only_books_ids if only_books_ids else None,
        lcc_shelves=lcc_shelves,
    )
    if not len(filtered_books):
        critical_error(
            "Unable to proceed. Combination of languages, "
            "books, formats and LCC shelves has no result."
        )

    # Get list of languages from catalog entries
    book_languages = (
        languages
        if languages
        else list({lang for book in filtered_books for lang in book.languages})
    )
    if len(book_languages) > 1 and with_fulltext_index:
        logger.warning(
            "Full text index with multiple languages in a single ZIM does not work "
            "well. You should probably disable full-text index with --no-index "
            "argument."
        )
    progress.increase_progress()

    # Build ZIM file
    logger.info("BUILDING ZIM")

    build_zimfile(
        output_folder=output_folder,
        books=filtered_books,
        mirror_url=mirror_url,
        concurrency=concurrency,
        languages=book_languages,
        zim_languages=(
            [lang.strip() for lang in zim_languages.split(",")]
            if (zim_languages := arguments.get("--zim-languages"))
            else None
        ),
        formats=formats,
        is_selection=len(only_books_ids) > 0 or len(lcc_shelves or []) > 0,
        zim_file=Path(zim_file).name if zim_file else None,
        zim_name=zim_name,
        title=zim_title,
        description=description,
        long_description=long_description,
        publisher=publisher,
        force=force,
        title_search=title_search,
        add_lcc_shelves=add_lcc_shelves,
        progress=progress,
        with_fulltext_index=with_fulltext_index,
        debug=debug,
        ui_dist=ui_dist,
    )

    # Final increase to indicate we are done
    progress.increase_progress()
    run_all()  # force flushing scraper progress to file

    logger.info("Scraper has finished normally")
