import datetime
import pathlib

from kiwixstorage import KiwixStorage
from peewee import fn

from gutenberg2zim.constants import logger
from gutenberg2zim.database import Book
from gutenberg2zim.export import export_all_books
from gutenberg2zim.iso639 import ISO_MATRIX
from gutenberg2zim.l10n import metadata_translations
from gutenberg2zim.shared import Global
from gutenberg2zim.utils import get_project_id


def build_zimfile(
    output_folder: pathlib.Path,
    download_cache: pathlib.Path,
    concurrency: int,
    languages: list[str],
    formats: list[str],
    only_books: list[int],
    s3_storage: KiwixStorage | None,
    optimizer_version: dict[str, str],
    zim_name: str | None,
    title: str | None,
    description: str | None,
    long_description: str | None,
    stats_filename: str | None,
    publisher: str,
    *,
    force: bool,
    title_search: bool,
    add_bookshelves: bool,
) -> None:
    # actual list of languages with books sorted by most used
    nb = fn.COUNT(Book.language).alias("nb")
    db_languages = [
        book.language
        for book in Book.select(Book.language, nb)
        .group_by(Book.language)
        .order_by(nb.desc())
    ]

    if languages:
        # user requested some languages, limit db-collected ones to matching
        languages = [lang for lang in db_languages if lang in languages]
    else:
        languages = db_languages
    iso_languages = [ISO_MATRIX.get(lang, lang) for lang in languages]

    formats.sort()

    metadata_lang = "mul" if len(iso_languages) > 1 else iso_languages[0]

    title = title or metadata_translations.get(metadata_lang, {}).get(
        "title", "Project Gutenberg Library"
    )
    # check if user has description input otherwise assign default description
    description = description or metadata_translations.get(metadata_lang, {}).get(
        "description",
        f'All books in "{iso_languages[0]}" language '
        "from the first producer of free Ebooks",
    )

    logger.info(f"\tWritting ZIM for {title}")

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
            download_cache=download_cache,
            concurrency=concurrency,
            languages=languages,
            formats=formats,
            only_books=only_books,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version,
            stats_filename=stats_filename,
            force=force,
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
