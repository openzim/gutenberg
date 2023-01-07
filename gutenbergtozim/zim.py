#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

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
    create_index=True,
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
        zim_name = "{}.zim".format(project_id)
    zim_path = output_folder.joinpath(zim_name)

    if path(zim_name).exists() and not force:
        logger.info("ZIM file `{}` already exist.".format(zim_name))
        return

    languages = [ISO_MATRIX.get(lang, lang) for lang in languages]
    languages.sort()

    Global.setup(
        filename=zim_path,
        language=",".join(languages),
        title=title,
        description=description,
        name=project_id,
    )

    Global.start()

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

    Global.finish()

    # cmd = [
    #     "zimwriterfs",
    #     "--zstd",
    #     "--welcome",
    #     "Home.html",
    #     "--favicon",
    #     "favicon.png",
    #     "--language",
    #     ",".join(languages),
    #     "--name",
    #     project_id,
    #     "--title",
    #     title,
    #     "--description",
    #     description,
    #     "--creator",
    #     "gutenberg.org",
    #     "--tags",
    #     "_category:gutenberg;gutenberg",
    #     "--publisher",
    #     "Kiwix",
    #     "--scraper",
    #     "gutengergtozim-{v}".format(v=VERSION),
    #     "--verbose",
    #     static_folder,
    #     six.text_type(zim_path),
    # ]

    # if not create_index:
    #     cmd.insert(1, "--withoutFTIndex")
    # zimwriterfs = subprocess.run(cmd)
    # if zimwriterfs.returncode == 0:
    #     logger.info("Successfuly created ZIM file at {}".format(zim_path))
    # else:
    #     logger.error("Unable to create ZIM file :(")
    #     raise SystemExit(zimwriterfs.returncode)
