#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
from path import Path as path

from gutenbergtozim import logger
from gutenbergtozim.export import export_all_books
from gutenbergtozim.iso639 import ISO_MATRIX
from gutenbergtozim.shared import Global
from gutenbergtozim.utils import FORMAT_MATRIX, get_project_id


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

    if not languages:
        languages = ["mul"]

    languages.sort()
    formats.sort()

    if title is None:
        if len(languages) > 5:
            title = "Project Gutenberg Library"
        else:
            title = "Project Gutenberg Library ({langs})".format(
                langs=",".join(languages)
            )

        if len(formats) < len(FORMAT_MATRIX):
            title += " with {formats}".format(formats=",".join(formats))

    logger.info("\tWritting ZIM for {}".format(title))

    if description is None:
        description = "The first producer of free ebooks"

    project_id = get_project_id(languages, formats, only_books)

    if zim_name is None:
        zim_name = "{}_{}.zim".format(
            project_id, datetime.datetime.now().strftime("%Y-%m"))
    zim_path = output_folder.joinpath(zim_name)

    if path(zim_name).exists() and not force:
        logger.info("ZIM file `{}` already exist.".format(zim_name))
        return

    iso_languages = [ISO_MATRIX.get(lang, lang) for lang in languages]
    iso_languages.sort()

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
