import os
import sys

from docopt import docopt
from path import Path

from gutenberg2zim.checkdeps import check_dependencies
from gutenberg2zim.constants import VERSION, logger
from gutenberg2zim.database import setup_database
from gutenberg2zim.download import download_all_books
from gutenberg2zim.rdf import download_rdf_file, get_rdf_fpath, parse_and_fill
from gutenberg2zim.s3 import s3_credentials_ok
from gutenberg2zim.urls import setup_urls
from gutenberg2zim.zim import build_zimfile

help_info = (
    """Usage: gutenberg2zim [-y] [-F] [-l LANGS] [-f FORMATS] """
    """[-d CACHE_PATH] [-e STATIC_PATH] """
    """[-z ZIM_PATH] [-u RDF_URL] [-b BOOKS] """
    """[-t ZIM_TITLE] [-n ZIM_DESC] """
    """[-c CONCURRENCY] [--dlc CONCURRENCY] [--no-index] """
    """[--prepare] [--parse] [--download] [--export] [--dev] """
    """[--zim] [--complete] [-m ONE_LANG_ONE_ZIM_FOLDER] """
    """[--title-search] [--bookshelves] [--optimization-cache S3URL] """
    """[--stats-filename STATS_FILENAME]"""
    """

-h --help                       Display this help message
-y --wipe-db                    Empty cached book metadata
-F --force                      Redo step even if target already exist

-l --languages=<list>           Comma-separated list of lang codes to filter"""
    """ export to (preferably ISO 639-1, else ISO 639-3)
-f --formats=<list>             Comma-separated list of formats to filter """
    """export to (epub, html, pdf, all)

-e --static-folder=<folder>     Use-as/Write-to this folder static HTML
-z --zim-file=<file>            Write ZIM into this file path
-t --zim-title=<title>          Set ZIM title
-n --zim-desc=<description>     Set ZIM description
-d --dl-folder=<folder>         Folder to use/write-to downloaded ebooks
-u --rdf-url=<url>              Alternative rdf-files.tar.bz2 URL
-b --books=<ids>                Execute the processes for specific books, """
    """separated by commas, or dashes for intervals
-c --concurrency=<nb>           Number of concurrent process for processing """
    """tasks
--dlc=<nb>                      Number of concurrent *download* process for """
    """download (overwrites --concurrency). """
    """if server blocks high rate requests
-m --one-language-one-zim=<folder> When more than 1 language, do one zim for each """
    """language (and one with all)
--no-index                      Do NOT create full-text index within ZIM file
--check                         Check dependencies
--prepare                       Download rdf-files.tar.bz2
--parse                         Parse all RDF files and fill-up the DB
--download                      Download ebooks based on filters
--zim                           Create a ZIM file
--title-search                  Add field to search a book by title and directly """
    """jump to it
--bookshelves                   Add bookshelves
--optimization-cache=<url>      URL with credentials to S3 bucket for using as """
    """optimization cache
--use-any-optimized-version     Try to use any optimized version found on """
    """optimization cache
--stats-filename=<filename>  Path to store the progress JSON file to

This script is used to produce a ZIM file (and any intermediate state)
of Gutenberg repository using a mirror."""
)


def main():
    arguments = docopt(help_info, version=VERSION)

    # optimizer version to use
    optimizer_version = {"html": "v1", "epub": "v1", "cover": "v1"}

    # actions constants
    do_prepare = arguments.get("--prepare", False)
    do_parse = arguments.get("--parse", False)
    do_download = arguments.get("--download", False)
    do_zim = arguments.get("--zim", False)
    do_checkdeps = arguments.get("--check", False)
    one_lang_one_zim_folder = arguments.get("--one-language-one-zim") or None
    complete_dump = arguments.get("--complete", False)

    zim_name = arguments.get("--zim-file")
    wipe_db = arguments.get("--wipe-db") or False
    rdf_url = (
        arguments.get("--rdf-url")
        or "http://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2"
    )
    dl_cache = arguments.get("--dl-folder") or os.path.join("dl-cache")
    books = arguments.get("--books") or ""
    zim_title = arguments.get("--zim-title")
    zim_desc = arguments.get("--zim-desc")
    concurrency = int(arguments.get("--concurrency") or 16)
    dl_concurrency = int(arguments.get("--dlc") or concurrency)
    force = arguments.get("--force", False)
    title_search = arguments.get("--title-search", False)
    bookshelves = arguments.get("--bookshelves", False)
    optimization_cache = arguments.get("--optimization-cache") or None
    use_any_optimized_version = arguments.get("--use-any-optimized-version", False)
    stats_filename = arguments.get("--stats-filename") or None

    s3_storage = None
    if optimization_cache:
        s3_storage = s3_credentials_ok(optimization_cache)
        if not s3_storage:
            raise ValueError("Unable to connect to Optimization Cache. Check its URL.")
        logger.info("S3 Credentials OK. Continuing ... ")

    # create tmp dir
    Path("tmp").mkdir_p()

    languages = [
        x.strip().lower()
        for x in (arguments.get("--languages") or "").split(",")
        if x.strip()
    ]
    # special shortcuts for "all"
    formats: list[str]
    if arguments.get("--formats") in ["all", None]:
        formats = ["epub", "pdf", "html"]
    else:
        formats = list(
            {
                x.strip().lower()
                for x in (arguments.get("--formats") or "").split(",")
                if x.strip()
            }
        )

    try:
        books = list(books.split(","))

        def f(x):
            return list(map(int, [i for i in x.split("-") if i.isdigit()]))

        books = []
        for i in books:
            blst = f(i)
            if len(blst) > 1:
                blst = range(blst[0], blst[1] + 1)
            books.extend(blst)
        books = list(set(books))
    except Exception as e:
        logger.error(e)
        books = []

    # no arguments, default to --complete
    if not (do_prepare + do_parse + do_download + do_zim):
        complete_dump = True

    if complete_dump:
        do_checkdeps = do_prepare = do_parse = do_download = do_zim = True

    if do_checkdeps:
        logger.info("CHECKING for dependencies on the system")
        if not check_dependencies()[0]:
            logger.error("Exiting...")
            sys.exit(1)

    rdf_path = get_rdf_fpath()

    if do_prepare:
        logger.info(f"PREPARING rdf-files cache from {rdf_url}")
        download_rdf_file(rdf_url=rdf_url, rdf_path=rdf_path)

    if wipe_db:
        logger.info("RESETING DATABASE IF EXISTS")
    logger.info("SETTING UP DATABASE")
    setup_database(wipe=wipe_db)

    if do_parse:
        logger.info(f"PARSING rdf-files in {rdf_path}")
        parse_and_fill(rdf_path=rdf_path, only_books=books)
        logger.info("Add possible url to db")
        setup_urls(force=force)

    if do_download:
        logger.info("DOWNLOADING ebooks from mirror using filters")
        download_all_books(
            download_cache=dl_cache,
            concurrency=dl_concurrency,
            languages=languages,
            formats=formats,
            only_books=books,
            force=force,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version
            if not use_any_optimized_version
            else None,
        )
    if one_lang_one_zim_folder:
        if languages == []:
            zims = []
            from gutenberg2zim.database import Book

            for book in Book.select(Book.language).distinct():
                zims.append([book.language])
            zims.append([])
        else:
            zims = [[lang] for lang in languages] + [languages]
    else:
        zims = [languages]

    for zim_lang in zims:
        if do_zim:
            logger.info("BUILDING ZIM dynamically")
            build_zimfile(
                output_folder=Path(one_lang_one_zim_folder or ".").abspath(),
                download_cache=dl_cache,
                concurrency=concurrency,
                languages=zim_lang,
                formats=formats,
                only_books=books,
                force=force,
                title_search=title_search,
                add_bookshelves=bookshelves,
                s3_storage=s3_storage,
                optimizer_version=optimizer_version,
                zim_name=Path(zim_name).name if zim_name else None,
                title=zim_title,
                description=zim_desc,
                stats_filename=stats_filename,
            )
