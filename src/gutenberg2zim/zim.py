import datetime

from path import Path
from peewee import fn

from gutenberg2zim.constants import logger
from gutenberg2zim.database import Book
from gutenberg2zim.export import export_all_books
from gutenberg2zim.iso639 import ISO_MATRIX
from gutenberg2zim.l10n import metadata_translations
from gutenberg2zim.shared import Global
from gutenberg2zim.utils import get_project_id


def build_zimfile(
    output_folder,
    download_cache,
    concurrency,
    languages,
    formats,
    only_books,
    force,
    title_search,
    add_bookshelves,
    s3_storage,
    optimizer_version,
    zim_name,
    title,
    description,
    stats_filename,
):
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

    title = title or metadata_translations.get(iso_languages[0], {}).get(
        "title", "Project Gutenberg Library"
    )
    description = description or metadata_translations.get(iso_languages[0], {}).get(
        "description", "The first producer of Free Ebooks"
    )
    logger.info(f"\tWritting ZIM for {title}")

    project_id = get_project_id(languages, formats, only_books)

    if zim_name is None:
        zim_name = "{}_{}.zim".format(
            project_id, datetime.datetime.now().strftime("%Y-%m")  # noqa: DTZ005
        )
    zim_path = output_folder.joinpath(zim_name)

    if Path(zim_name).exists() and not force:
        logger.info(f"ZIM file `{zim_name}` already exist.")
        return
    elif Path(zim_name).exists():
        logger.info(f"Removing existing ZIM file {zim_name}")
        Path(zim_name).unlink()

    Global.setup(
        filename=zim_path,
        language=",".join(iso_languages),
        title=title,
        description=description,
        name=project_id,
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
            force=force,
            title_search=title_search,
            add_bookshelves=add_bookshelves,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version,
            stats_filename=stats_filename,
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
