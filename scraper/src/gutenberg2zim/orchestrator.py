"""Scrape orchestration (split out of `entrypoint.py`).

`run_scrape(config)` is everything between "CLI arguments parsed into a
`ScrapeConfig`" and "ZIM written": logging setup, i18n, CSV catalog
download/load/filter, language derivation, and `build_zimfile` (moved here
from the deleted `zim.py`), which creates the `ZimAssembler` and drives the
`GutenbergPipeline`.
"""

import datetime
import logging
from dataclasses import replace
from pathlib import Path

from gutenberg2zim.config import ScrapeConfig
from gutenberg2zim.constants import logger
from gutenberg2zim.core import i18n
from gutenberg2zim.core.exporters.ui_dist_exporter import export_ui_dist
from gutenberg2zim.core.language import (
    ISO_MATRIX,
    ISO_MATRIX_REV,
    get_zim_language_metadata,
)
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.core.progress import ScraperProgress
from gutenberg2zim.core.utils import critical_error, get_zim_name
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler
from gutenberg2zim.sources.gutenberg.adapters import GUTENBERG_SOURCE
from gutenberg2zim.sources.gutenberg.catalog import (
    CatalogEntry,
    download_csv_file,
    filter_books,
    get_csv_fpath,
    load_catalog,
)
from gutenberg2zim.sources.gutenberg.metadata import GutenbergRdfMetadata
from gutenberg2zim.sources.gutenberg.pipeline import GutenbergPipeline


def run_scrape(config: ScrapeConfig) -> None:
    """Run the whole scrape described by `config`"""
    if config.debug:
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    i18n.setup_i18n()

    csv_path = get_csv_fpath()

    progress = ScraperProgress(config.stats_filename)
    progress.increase_total(1)

    # Download CSV catalog
    csv_url = f"{config.mirror_url}/cache/epub/feeds/pg_catalog.csv.gz"
    logger.info(f"PREPARING CSV catalog from {csv_url}")
    download_csv_file(csv_path=csv_path, csv_url=csv_url)

    # Load catalog and filter books
    logger.info(f"LOADING catalog from {csv_path}")
    catalog = load_catalog(csv_path)

    # Filter books based on languages, specific book IDs, and LCC shelves
    filtered_books = filter_books(
        catalog=catalog,
        languages=config.languages if config.languages else None,
        only_books=[int(book_id) for book_id in config.books] if config.books else None,
        lcc_shelves=config.collections,
    )
    if not len(filtered_books):
        critical_error(
            "Unable to proceed. Combination of languages, "
            "books, formats and LCC shelves has no result."
        )

    # Get list of languages from catalog entries
    book_languages = (
        config.languages
        if config.languages
        else list({lang for book in filtered_books for lang in book.languages})
    )
    if len(book_languages) > 1 and config.with_fulltext_index:
        logger.warning(
            "Full text index with multiple languages in a single ZIM does not work "
            "well. You should probably disable full-text index with --no-index "
            "argument."
        )
    progress.increase_progress()

    # Build ZIM file
    logger.info("BUILDING ZIM")

    work_store = WorkStore()

    build_zimfile(
        books=filtered_books,
        config=replace(config, languages=book_languages),
        work_store=work_store,
        progress=progress,
    )

    # Final increase to indicate we are done
    progress.increase_progress()
    progress.report_progress()  # force flushing scraper progress to file

    logger.info("Scraper has finished normally")


def build_zimfile(
    books: list[CatalogEntry],
    config: ScrapeConfig,
    work_store: WorkStore,
    progress: ScraperProgress,
) -> None:
    """Build ZIM file from the works collected in the work store"""
    progress.increase_total(len(books))
    output_folder = config.output_folder
    mirror_url = config.mirror_url
    concurrency = config.concurrency
    languages = config.languages or []
    formats = config.formats
    debug = config.debug
    zim_file = config.zim_file
    zim_name = config.zim_name
    title = config.title
    description = config.description
    long_description = config.long_description
    zim_languages = config.zim_languages
    publisher = config.publisher
    ui_dist = config.ui_dist
    # build_scrape_config always resolves ui_dist (CLI arg, env var, or default)
    assert ui_dist is not None  # noqa: S101
    primary_color = config.primary_color
    secondary_color = config.secondary_color
    overwrite = config.overwrite
    is_selection = config.is_selection
    title_search = config.title_search
    add_lcc_shelves = config.add_lcc_shelves
    with_fulltext_index = config.with_fulltext_index
    iso_languages = [ISO_MATRIX.get(lang, lang) for lang in languages]

    formats.sort()

    metadata_lang = "mul" if len(iso_languages) > 1 else iso_languages[0]

    metadata_locales_lang = ISO_MATRIX_REV.get(metadata_lang, metadata_lang)

    i18n.change_locale(metadata_locales_lang)

    title = title or i18n.t("metadata_defaults.title")
    # check if user has description input otherwise assign default description
    description = description or i18n.t(
        "metadata_defaults.description",
        f'All books in "{iso_languages[0]}" language from the first producer of free'
        " Ebooks",
    )

    logger.info(f"\tWriting {metadata_lang} ZIM for {title}")

    zim_name = zim_name or get_zim_name(languages, formats, is_selection)

    if zim_file is None:
        zim_file = "{}_{}.zim".format(
            zim_name,
            datetime.datetime.now().strftime("%Y-%m"),  # noqa: DTZ005
        )
        zim_path = output_folder / zim_file
    else:
        zim_path = Path(zim_file)
        if not zim_path.is_absolute() and zim_path.parent == Path("."):
            # Just a filename, put it in output_folder
            zim_path = output_folder / zim_path

    # Ensure the output folder exists before creating the ZIM
    zim_path.parent.mkdir(parents=True, exist_ok=True)

    if zim_path.exists() and not overwrite:
        logger.info(f"ZIM file `{zim_file}` already exist.")
        return
    elif zim_path.exists():
        logger.info(f"Removing existing ZIM file {zim_file}")
        zim_path.unlink(missing_ok=True)

    assembler = ZimAssembler(
        filename=zim_path,
        language=zim_languages or get_zim_language_metadata(languages, books),
        title=title,
        description=description,
        long_description=long_description,
        name=zim_name,
        publisher=publisher,
        source_creator="gutenberg.org",
        tags="_category:gutenberg;gutenberg",
        with_fulltext_index=with_fulltext_index,
        debug=debug,
    )

    assembler.start()

    try:
        # Discovery already happened in the entrypoint (it needs the filtered
        # catalog entries for language metadata, the empty-result error and
        # the progress total), so the pipeline receives ready-made refs
        refs = [
            WorkRef(
                id=str(book.book_id),
                source=GUTENBERG_SOURCE,
                extra={"languages": book.languages, "lcc_shelf": book.lcc_shelf},
            )
            for book in books
        ]
        pipeline = GutenbergPipeline(
            metadata=GutenbergRdfMetadata(mirror_url),
            store=work_store,
            assembler=assembler,
            progress=progress,
            concurrency=concurrency,
            formats=formats,
            zim_name=zim_name,
            title=title,
            description=description,
            add_lcc_shelves=add_lcc_shelves,
            primary_color=primary_color,
            secondary_color=secondary_color,
            mirror_url=mirror_url,
            title_search=title_search,
        )
        pipeline.run(refs)

        # Export Vue.js UI dist folder
        export_ui_dist(ui_dist, title, assembler)

    except KeyboardInterrupt:
        assembler.can_finish = False
        logger.error("KeyboardInterrupt, exiting.")
        raise
    except Exception:
        assembler.can_finish = False
        logger.exception("Interrupting process due to error")
        raise
    else:
        assembler.finish()
