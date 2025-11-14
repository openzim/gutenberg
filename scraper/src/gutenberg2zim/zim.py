import datetime
import pathlib
import re

from gutenberg2zim import i18n
from gutenberg2zim.book_processor import process_all_books
from gutenberg2zim.constants import logger
from gutenberg2zim.csv_catalog import CatalogEntry
from gutenberg2zim.iso639 import ISO_MATRIX, ISO_MATRIX_REV, ZIM_LANGUAGES_MAP
from gutenberg2zim.scraper_progress import ScraperProgress
from gutenberg2zim.shared import Global
from gutenberg2zim.utils import get_zim_name


def get_zim_language_metadata(languages: list[str], books: list[CatalogEntry]):
    language_counts = {
        zim_lang: sum(lang in book.languages for book in books)
        for lang in languages
        for zim_lang in ZIM_LANGUAGES_MAP.get(lang, [ISO_MATRIX.get(lang, None)])
        if zim_lang
    }
    return sorted(language_counts, key=lambda lang: language_counts[lang], reverse=True)


def export_ui_dist(ui_dist: pathlib.Path, title: str) -> None:
    """Export Vue.js UI dist folder to ZIM file."""
    if not ui_dist.exists():
        logger.warning(f"UI dist directory not found at {ui_dist}, skipping UI export")
        return

    logger.info(f"Adding Vue.js UI files from {ui_dist}")
    for file in ui_dist.rglob("*"):
        if file.is_dir():
            continue
        path = str(file.relative_to(ui_dist))
        logger.debug(f"Adding {path} to ZIM")

        # Update index.html title
        if path == "index.html":
            html_content = file.read_text(encoding="utf-8")
            new_html_content = re.sub(
                r"(<title>)(.*?)(</title>)",
                rf"\1{title}\3",
                html_content,
                flags=re.IGNORECASE,
            )
            Global.add_item_for(
                path=path,
                content=new_html_content,
                mimetype="text/html",
                is_front=True,
            )
        else:
            Global.add_item_for(
                path=path,
                fpath=file,
                is_front=False,
            )


def build_zimfile(
    books: list[CatalogEntry],
    output_folder: pathlib.Path,
    mirror_url: str,
    concurrency: int,
    languages: list[str],
    formats: list[str],
    zim_file: str | None,
    zim_name: str | None,
    title: str | None,
    description: str | None,
    long_description: str | None,
    zim_languages: list[str] | None,
    publisher: str,
    *,
    force: bool,
    is_selection: bool,
    title_search: bool,
    add_lcc_shelves: bool,
    progress: ScraperProgress,
    with_fulltext_index: bool,
    debug: bool,
    ui_dist: pathlib.Path | None = None,
) -> None:
    """Build ZIM file using singleton BookRepository"""
    progress.increase_total(len(books))
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
            zim_name, datetime.datetime.now().strftime("%Y-%m")  # noqa: DTZ005
        )
    zim_path = output_folder / zim_file

    if zim_path.exists() and not force:
        logger.info(f"ZIM file `{zim_file}` already exist.")
        return
    elif zim_path.exists():
        logger.info(f"Removing existing ZIM file {zim_file}")
        zim_path.unlink(missing_ok=True)

    Global.setup(
        filename=zim_path,
        language=zim_languages or get_zim_language_metadata(languages, books),
        title=title,
        description=description,
        long_description=long_description,
        name=zim_name,
        publisher=publisher,
        with_fulltext_index=with_fulltext_index,
        debug=debug,
    )

    Global.start()

    try:
        process_all_books(
            book_ids=[book.book_id for book in books],
            zim_name=zim_name,
            mirror_url=mirror_url,
            concurrency=concurrency,
            languages=languages,
            formats=formats,
            progress=progress,
            title_search=title_search,
            add_lcc_shelves=add_lcc_shelves,
            title=title,
            description=description,
        )

        # Export Vue.js UI dist folder if provided
        if ui_dist:
            export_ui_dist(ui_dist, title or i18n.t("metadata_defaults.title"))

    except Exception as exc:
        # request Creator not to create a ZIM file on finish
        Global.creator.can_finish = False
        if isinstance(exc, KeyboardInterrupt):
            logger.error("KeyboardInterrupt, exiting.")
        else:
            logger.error(f"Interrupting process due to error: {exc}")
            logger.exception(exc)
        return
    else:
        Global.finish()
