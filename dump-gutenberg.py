#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os

from docopt import docopt

from gutenberg import logger
from gutenberg.database import db
from gutenberg.rdf import setup_rdf_folder, parse_and_fill

help = """Usage: dump-gutenberg.py [-f RDF_FOLDER] [-m URL_MIRROR] """ \
       """[--prepare] [--parse] [--download] [--export] [--zim] [--complete]

-h --help                   Display this help message
-m --mirror URL_MIRROR      Use URL as base for all downloads.
-f --rdf-folder RDF_FOLDER  Don't download rdf-files.tar.bz2 and use extracted folder instead

--prepare                   Download & extract rdf-files.tar.bz2
--parse                     Parse all RDF files and fill-up the DB
--download                  Download ebooks based on filters
--export                    Export downloaded content to zim-friendly static HTML
--zim                       Create a ZIM file

This script is used to produce a ZIM file (and any intermediate state)
of Gutenberg repository using a mirror."""

def main(arguments):

    from pprint import pprint as pp ; pp(arguments)

    # actions constants
    DO_PREPARE = arguments.get('--prepare', False)
    DO_PARSE = arguments.get('--parse', False)
    DO_DOWNLOAD = arguments.get('--download', False)
    DO_EXPORT = arguments.get('--export', False)
    DO_ZIM = arguments.get('--zim', False)
    COMPLETE_DUMP = arguments.get('--complete', False)

    URL_MIRROR = arguments.get('URL_MIRROR', 'http://zimfarm.kiwix.org/gutenberg')
    RDF_FOLDER = arguments.get('RDF_FOLDER')
    RDF_URL = arguments.get('RDF_URL', 'http://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2')

    if COMPLETE_DUMP:
        DO_PREPARE = DO_PARSE = DO_DOWNLOAD = DO_EXPORT = DO_ZIM = True

    if DO_PREPARE or RDF_FOLDER is None:
        logger.info("PREPARING rdf-files cache from {}".format(RDF_URL))
        RDF_FOLDER = os.path.join('rdf-files')
        setup_rdf_folder(RDF_URL, RDF_FOLDER)

    if DO_PARSE:
        logger.info("PARSING rdf-files in {}".format(RDF_FOLDER))
        parse_and_fill(RDF_FOLDER)


if __name__ == '__main__':
    main(docopt(help, version=0.1))
