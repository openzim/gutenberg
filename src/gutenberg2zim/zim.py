import datetime
import pathlib

from gutenberg2zim import i18n
from gutenberg2zim.constants import logger
from gutenberg2zim.export import export_all_books
from gutenberg2zim.iso639 import ISO_MATRIX, ISO_MATRIX_REV
from gutenberg2zim.models import repository
from gutenberg2zim.scraper_progress import ScraperProgress
from gutenberg2zim.shared import Global
from gutenberg2zim.utils import get_project_id


def existing_and_sorted_languages(
    languages: list[str] | None, books_ids: list[int] | None
) -> list[str]:
    """Get list of languages sorted by number of books from singleton BookRepository"""

    # actual list of languages with books sorted by most used
    db_languages = repository.get_languages_sorted_by_count(only_books=books_ids)

    if languages:
        # user requested some languages, limit db-collected ones to matching
        existing_and_sorted_languages = [
            lang for lang in db_languages if lang in languages
        ]
    else:
        existing_and_sorted_languages = db_languages

    return existing_and_sorted_languages


def build_zimfile(
    output_folder: pathlib.Path,
    mirror_url: str,
    concurrency: int,
    languages: list[str],
    formats: list[str],
    only_books: list[int],
    zim_name: str | None,
    title: str | None,
    description: str | None,
    long_description: str | None,
    publisher: str,
    *,
    force: bool,
    title_search: bool,
    add_bookshelves: bool,
    progress: ScraperProgress,
) -> None:
    """Build ZIM file using singleton BookRepository"""
    progress.increase_total(len(repository.books))
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

    project_id = get_project_id(languages, formats, only_books)

    if zim_name is None:
        zim_name = "{}_{}.zim".format(
            project_id, datetime.datetime.now().strftime("%Y-%m")  # noqa: DTZ005
        )
    zim_path = output_folder / zim_name

    if zim_path.exists() and not force:
        logger.info(f"ZIM file `{zim_name}` already exist.")
        return
    elif zim_path.exists():
        logger.info(f"Removing existing ZIM file {zim_name}")
        zim_path.unlink(missing_ok=True)

    Global.setup(
        filename=zim_path,
        language=iso_languages,
        title=title,
        description=description,
        long_description=long_description,
        name=project_id,
        publisher=publisher,
    )

    Global.start()

    try:
        export_all_books(
            project_id=project_id,
            mirror_url=mirror_url,
            concurrency=concurrency,
            languages=languages,
            formats=formats,
            progress=progress,
            title_search=title_search,
            add_bookshelves=add_bookshelves,
        )

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

    logger.info("Scraper has finished normally")
