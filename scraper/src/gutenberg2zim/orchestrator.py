"""Scrape orchestration (split out of `entrypoint.py`).

`run_scrape(config)` is everything between "CLI arguments parsed into a
`ScrapeConfig`" and "ZIM written": logging setup, i18n, CSV catalog
download/load/filter, language derivation, and `build_zimfile` (moved here
from the deleted `zim.py`), which creates the `ZimAssembler` and drives the
source's `Pipeline` resolved from the registry profile.
"""

import datetime
import logging
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from gutenberg2zim.config import ScrapeConfig
from gutenberg2zim.constants import logger
from gutenberg2zim.core import i18n
from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.exporters.ui_dist_exporter import export_ui_dist
from gutenberg2zim.core.language import (
    ISO_MATRIX,
    ISO_MATRIX_REV,
    HasLanguages,
    get_zim_language_metadata,
)
from gutenberg2zim.core.ports import (
    CatalogFilters,
    CatalogPort,
    WorkRef,
)
from gutenberg2zim.core.progress import ScraperProgress
from gutenberg2zim.core.utils import critical_error, get_zim_name
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler
from gutenberg2zim.sources.registry import SourceProfile, get_source


def run_scrape(config: ScrapeConfig) -> None:
    """Run the whole scrape described by `config`"""
    if config.debug:
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    profile = get_source(config.source)
    i18n.setup_i18n(profile.locale_namespace)

    progress = ScraperProgress(config.stats_filename)
    progress.increase_total(1)
    engine = DownloadEngine(cache_dir=config.cache_dir)
    try:
        if isinstance(profile.catalog, type):
            catalog_factory = cast(Callable[..., CatalogPort], profile.catalog)
            catalog = catalog_factory(
                engine,
                base_url=config.mirror_url,
                cache_dir=config.cache_dir,
                refresh_catalog=bool(config.source_options.get("refresh_catalog")),
            )
            if profile.handle_cli_action(catalog, config.source_options):
                return
            filtered_books = list(
                catalog.discover(
                    CatalogFilters(
                        languages=config.languages,
                        book_ids=config.books,
                        collections=config.collections,
                        formats=config.formats,
                        options=config.source_options,
                    )
                )
            )
        else:
            catalog = profile.catalog
            csv_path = catalog.get_csv_fpath()
            csv_url = f"{config.mirror_url.rstrip('/')}{profile.catalog_feed_path}"
            logger.info(f"PREPARING CSV catalog from {csv_url}")
            catalog.download_csv_file(csv_path=csv_path, csv_url=csv_url, engine=engine)
            logger.info(f"LOADING catalog from {csv_path}")
            catalog_entries = catalog.load_catalog(csv_path)
            filtered_books = catalog.filter_books(
                catalog=catalog_entries,
                languages=config.languages if config.languages else None,
                only_books=(
                    [int(book_id) for book_id in config.books] if config.books else None
                ),
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
            else list(
                {
                    lang
                    for book in filtered_books
                    for lang in (
                        book.extra.get("languages", [])
                        if isinstance(book, WorkRef)
                        else book.languages
                    )
                }
            )
        )
        if len(book_languages) > 1 and config.with_fulltext_index:
            logger.warning(
                "Full text index with multiple languages in a single ZIM does not "
                "work well. You should probably disable full-text index with "
                "--no-index argument."
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
            engine=engine,
            profile=profile,
        )

        # Final increase to indicate we are done
        progress.increase_progress()
        progress.report_progress()  # force flushing scraper progress to file

        logger.info("Scraper has finished normally")
    finally:
        engine.close()


def build_zimfile(
    books: Sequence[Any | WorkRef],
    config: ScrapeConfig,
    work_store: WorkStore,
    progress: ScraperProgress,
    engine: DownloadEngine,
    profile: SourceProfile,
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
    with_fulltext_index = config.with_fulltext_index
    iso_languages = [ISO_MATRIX.get(lang, lang) for lang in languages]

    formats.sort()

    metadata_lang = "mul" if len(iso_languages) > 1 else iso_languages[0]

    metadata_locales_lang = ISO_MATRIX_REV.get(metadata_lang, metadata_lang)

    i18n.change_locale(metadata_locales_lang)

    title = title or i18n.t(f"{profile.locale_namespace}.metadata_defaults.title")
    # check if user has description input otherwise assign default description
    description = description or i18n.t(
        f"{profile.locale_namespace}.metadata_defaults.description",
        f'All books in "{iso_languages[0]}" language from {profile.tagline}',
    )

    logger.info(f"\tWriting {metadata_lang} ZIM for {title}")

    zim_name = zim_name or get_zim_name(
        languages, formats, is_selection, prefix=profile.zim_name_prefix
    )

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
        language=zim_languages
        or get_zim_language_metadata(
            languages,
            cast(
                Sequence[HasLanguages],
                [
                    (
                        book
                        if not isinstance(book, WorkRef)
                        else SimpleNamespace(languages=book.extra.get("languages", []))
                    )
                    for book in books
                ],
            ),
        ),
        title=title,
        description=description,
        long_description=long_description,
        name=zim_name,
        publisher=publisher,
        source_creator=profile.source_creator,
        tags=profile.zim_tags,
        with_fulltext_index=with_fulltext_index,
        debug=debug,
    )

    assembler.start()

    try:
        # Discovery already happened in the entrypoint (it needs the filtered
        # catalog entries for language metadata, the empty-result error and
        # the progress total), so the pipeline receives ready-made refs
        refs = [
            (
                book
                if isinstance(book, WorkRef)
                else WorkRef(
                    id=str(book.book_id),
                    source=profile.slug,
                    extra={"languages": book.languages},
                )
            )
            for book in books
        ]
        pipeline = profile.pipeline_class(
            metadata=profile.metadata_class(
                mirror_url,
                engine=engine,
                **profile.metadata_options(config.cache_dir),
            ),
            store=work_store,
            assembler=assembler,
            progress=progress,
            concurrency=concurrency,
            formats=formats,
            zim_name=zim_name,
            title=title,
            description=description,
            primary_color=primary_color,
            secondary_color=secondary_color,
            display_name=profile.display_name,
            source_slug=profile.slug,
            source_description=profile.source_description,
            collection_label=profile.collection_label,
            collection_icon_style=profile.collection_icon_style,
            engine=engine,
            title_search=title_search,
            **profile.pipeline_options(mirror_url, config.cache_dir),
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
