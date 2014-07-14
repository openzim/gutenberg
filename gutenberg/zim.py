#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import re
import datetime

from gutenberg import logger
from gutenberg.utils import exec_cmd
from gutenberg.iso639 import ISO_MATRIX


def build_zimfile(static_folder, zim_path=None,
                  languages=[], formats=[],
                  title=None, description=None,
                  only_books=[]):

    if not languages:
        languages = ['mul']

    if title is None:
        if len(languages) > 5:
            title = ("Project Gutenberg Library with {formats}"
                     .format(formats=",".join(formats)))
        else:
            title = ("Project Gutenberg Library ({langs}) with {formats}"
                     .format(langs=",".join(languages),
                             formats=",".join(formats)))

    logger.info("\tWritting ZIM for {}".format(title))

    if description is None:
        description = "The first producer of free ebooks"

    if zim_path is None:
        if len(languages) > 1:
            zim_path = "gutenberg_all_{date}.zim".format(
                    date=datetime.datetime.now().strftime('%m_%Y'))
        else:
            zim_path = "gutenberg_{lang}_all_{date}.zim".format(
                    lang=languages[0],
                    date=datetime.datetime.now().strftime('%m_%Y'))

    context = {
        'languages': ','.join([ISO_MATRIX.get(lang, lang) for lang in languages]),
        'title': title,
        'description': description,
        'creator': 'gutenberg.org',
        'publisher': 'Kiwix',

        'home': 'Home.html',
        'favicon': 'favicon.png',

        'static': static_folder,
        'zim': zim_path
    }

    cmd = ('zimwriterfs --welcome=\\"{home}\\" --favicon=\\"{favicon}\\" '
           '--language=\\"{languages}\\" --title=\\"{title}\\" '
           '--description=\\"{description}\\" '
           '--creator=\\"{creator}\\" --publisher=\\"{publisher}\\" \\"{static}\\" \\"{zim}\\"'
           .format(**context))

    logger.debug("\t\t{}".format(re.sub('\\\\"','"',cmd)))
    if exec_cmd(cmd):
        logger.info("Successfuly created ZIM file at {}".format(zim_path))
    else:
        logger.error("Unable to create ZIM file :(")
