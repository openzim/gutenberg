#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import datetime

from gutenberg import logger
from gutenberg.utils import exec_cmd
from gutenberg.iso639 import ISO_MATRIX


def build_zimfile(static_folder, zim_path=None,
                  languages=[], formats=[],
                  title=None, description=None,
                  only_books=[]):

    if not languages:
        languages = ['en']

    if title is None:
        title = ("Project Gutenberg Library ({langs}) with {formats}"
                 .format(langs=",".join(languages),
                         formats=",".join(formats)))

    logger.info("\tWritting ZIM for {}".format(title))

    if description is None:
        description = "The first producer of free ebooks"

    if zim_path is None:
        zim_path = "gutenberg_{lang}_all_{date}.zim".format(
                lang=languages[0],
                date=datetime.datetime.now().strftime('%m_%Y'))

    context = {
        'languages': ISO_MATRIX.get(languages[0], languages[0]),
        'title': title,
        'description': description,
        'creator': "gutenberg.org",
        'publisher': "Kiwix",

        'home': 'Home.html',
        'favicon': 'favicon.png',

        'static': static_folder,
        'zim': zim_path
    }

    cmd = ('zimwriterfs --welcome={home} --favicon={favicon} '
           '--language={languages} --title=\\"{title}\\" '
           '--description=\\"{description}\\" '
           '--creator=\\"{creator}\\" --publisher=\\"{publisher}\\" {static} {zim}'
           .format(**context))

    logger.debug(cmd)
    return exec_cmd(cmd)

