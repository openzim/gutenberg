#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os

from docopt import docopt

from gutenberg import logger
from gutenberg.rdf import setup_rdf_folder, parse_and_fill
from gutenberg.download import download_all_books
from gutenberg.export import export_all_books
from gutenberg.zim import build_zimfile

help = """Usage: dump-gutenberg.py [-f RDF_FOLDER] [-m URL_MIRROR] """ \
       """[--prepare] [--parse] [--download] [--export] [--zim] [--complete]

-h --help                       Display this help message
-m --mirror=<url>               Use URL as base for all downloads.
-f --rdf-folder=<folder>        Don't download rdf-files.tar.bz2 and use extracted folder instead
-e --static-folder=<folder>     Use-as/Write-to this folder static HTML
-e --zim-file=<file>            Write ZIM into this file path

--prepare                       Download & extract rdf-files.tar.bz2
--parse                         Parse all RDF files and fill-up the DB
--download                      Download ebooks based on filters
--export                        Export downloaded content to zim-friendly static HTML
--zim                           Create a ZIM file

This script is used to produce a ZIM file (and any intermediate state)
of Gutenberg repository using a mirror."""

def main(arguments):

    # actions constants
    DO_PREPARE = arguments.get('--prepare', False)
    DO_PARSE = arguments.get('--parse', False)
    DO_DOWNLOAD = arguments.get('--download', False)
    DO_EXPORT = arguments.get('--export', False)
    DO_ZIM = arguments.get('--zim', False)
    COMPLETE_DUMP = arguments.get('--complete', False)

    URL_MIRROR = arguments.get('--mirror', 'http://zimfarm.kiwix.org/gutenberg')
    RDF_FOLDER = arguments.get('--rdf-folder')
    STATIC_FOLDER = arguments.get('--static-folder')
    ZIM_FILE = arguments.get('--zim-file', 'gutenberg.zim')
    RDF_URL = arguments.get('RDF_URL', 'http://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2')

    # no arguments, default to --complete
    if not (DO_PREPARE + DO_PARSE + DO_DOWNLOAD + DO_EXPORT + DO_ZIM):
        COMPLETE_DUMP = True

    if COMPLETE_DUMP:
        DO_PREPARE = DO_PARSE = DO_DOWNLOAD = DO_EXPORT = DO_ZIM = True

    if DO_PREPARE or RDF_FOLDER is None:
        logger.info("PREPARING rdf-files cache from {}".format(RDF_URL))
        RDF_FOLDER = os.path.join('rdf-files')
        setup_rdf_folder(RDF_URL, RDF_FOLDER)

    if DO_PARSE:
        logger.info("PARSING rdf-files in {}".format(RDF_FOLDER))
        parse_and_fill(RDF_FOLDER)

    if DO_DOWNLOAD:
        logger.info("DOWNLOADING ebooks from mirror using filters")
        download_all_books(URL_MIRROR)

    if DO_EXPORT:
        logger.info("EXPORTING ebooks to satic folder (and JSON)")
        export_all_books(STATIC_FOLDER)

    if DO_ZIM:
        logger.info("BUILDING ZIM off satic folder {}".format(STATIC_FOLDER))
        build_zimfile(STATIC_FOLDER, ZIM_FILE)

if __name__ == '__main__':
    main(docopt(help, version=0.1))
