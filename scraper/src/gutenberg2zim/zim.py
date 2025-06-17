import datetime
import pathlib
import shutil
import subprocess

from kiwixstorage import KiwixStorage
from peewee import fn

from gutenberg2zim.constants import PROJECT_ROOT, logger
from gutenberg2zim.database import BookLanguage
from gutenberg2zim.export import export_all_books
from gutenberg2zim.iso639 import ISO_MATRIX
from gutenberg2zim.l10n import metadata_translations
from gutenberg2zim.shared import Global, add_dist_folder_to_zim
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
) -> None:
    # actual list of languages with books sorted by most used
    nb = fn.COUNT(BookLanguage.book).alias("nb")
    db_languages = [
        lang.language_code
        for lang in BookLanguage.select(BookLanguage.language_code, nb)
        .group_by(BookLanguage.language_code)
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

    # zim dis resource
    dist_dir = pathlib.Path(PROJECT_ROOT / "zimui" / "dist")

    Global.start()

    try:

        # unoptimized->optimized
        export_all_books(
            download_cache=download_cache,
            concurrency=concurrency,
            languages=languages,
            formats=formats,
            only_books=only_books,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version,
            stats_filename=stats_filename,
            force=force,
        )

        # Trigger `yarn build` in the zimui frontend directory
        zimui_path = PROJECT_ROOT / "zimui"

        logger.info("Starting frontend build.")
        yarn_path = shutil.which("yarn")
        if yarn_path is None:
            raise RuntimeError("yarn not found")

        subprocess.run([yarn_path, "install"], cwd=zimui_path, check=True)
        logger.info("Dependencies installed.")

        subprocess.run([yarn_path, "build"], cwd=zimui_path, check=True)
        logger.info("Frontend build completed.")

        add_dist_folder_to_zim(dist_dir)

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
