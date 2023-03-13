#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
from path import Path as path

from peewee import fn

from gutenbergtozim import logger
from gutenbergtozim.database import Book
from gutenbergtozim.export import export_all_books
from gutenbergtozim.iso639 import ISO_MATRIX
from gutenbergtozim.l10n import metadata_translations
from gutenbergtozim.shared import Global
from gutenbergtozim.utils import get_project_id


def build_zimfile(
    output_folder,
    download_cache=None,
    concurrency=None,
    languages=[],
    formats=[],
    only_books=[],
    force=False,
    title_search=False,
    add_bookshelves=False,
    s3_storage=None,
    optimizer_version=None,
    zim_name=None,
    title=None,
    description=None,
    stats_filename=None,
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
    logger.info("\tWritting ZIM for {}".format(title))

    project_id = get_project_id(languages, formats, only_books)

    if zim_name is None:
        zim_name = "{}_{}.zim".format(
            project_id, datetime.datetime.now().strftime("%Y-%m")
        )
    zim_path = output_folder.joinpath(zim_name)

    if path(zim_name).exists() and not force:
        logger.info("ZIM file `{}` already exist.".format(zim_name))
        return
    elif path(zim_name).exists():
        logger.info(f"Removing existing ZIM file {zim_name}")
        path(zim_name).unlink()

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
