#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import re
import hashlib
from contextlib import contextmanager

import envoy
from path import path

from gutenberg import logger
from gutenberg.iso639 import language_name
from gutenberg.database import Book, BookFormat, Format


FORMAT_MATRIX = {
    'epub': 'application/epub+zip',
    'pdf': 'application/pdf',
    'html': 'text/html'
}

BAD_BOOKS_FORMATS = {
    39765: ['pdf'],
    40194: ['pdf'],
}


NB_MAIN_LANGS = 5


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(newdir)
    try:
        yield
    finally:
        os.chdir(prevdir)


def exec_cmd(cmd):
    # logger.debug("** {}".format(str(cmd.encode('utf-8'))))
    return envoy.run(str(cmd.encode('utf-8')))


def download_file(url, fname):
    output = "--output {}".format(fname) if fname else "--remote-name"
    cmd = ("curl --fail --insecure --location {output} --silent "
           "--show-error -C - --url {url}".format(output=output, url=url))
    # logger.debug("--/ {}".format(cmd))
    cmdr = exec_cmd(cmd)
    return cmdr.status_code == 0

def main_formats_for(book):
    fmts = [fmt.format.mime
            for fmt in BookFormat.select(BookFormat, Book, Format)
                                 .join(Book).switch(BookFormat)
                                 .join(Format)
                                 .where(Book.id == book.id)]
    return [k for k, v in FORMAT_MATRIX.items() if v in fmts]


def get_list_of_filtered_books(languages, formats, only_books=[]):
    if len(formats):
        qs = Book.select().join(BookFormat) \
                 .join(Format) \
                 .where(Format.mime << [FORMAT_MATRIX.get(f)
                                        for f in formats]) \
                 .group_by(Book.id)
    else:
        qs = Book.select()

    if len(only_books):
        print(only_books)
        qs = qs.where(Book.id << only_books)

    if len(languages):
        qs = qs.where(Book.language << languages)

    return qs


def get_langs_with_count(books):
    lang_count = {}
    for book in books:
        if not book.language in lang_count:
            lang_count[book.language] = 0
        lang_count[book.language] += 1

    return [(language_name(l), l, nb)
            for l, nb in sorted(lang_count.items(),
                                key=lambda x: x[1],
                                reverse=True)]


def get_lang_groups(books):
    langs_wt_count = get_langs_with_count(books)
    if len(langs_wt_count) <= NB_MAIN_LANGS:
        return langs_wt_count, []
    else:
        return (langs_wt_count[:NB_MAIN_LANGS],
                sorted(langs_wt_count[NB_MAIN_LANGS:], key=lambda x: x[0]))

def md5sum(fpath):
    with open(fpath, 'r') as f:
        return hashlib.md5(f.read()).hexdigest()


def is_bad_cover(fpath):
    bad_sizes = [19263]
    bad_sums = ['a059007e7a2e86f2bf92e4070b3e5c73']

    if path(fpath).size not in bad_sizes:
        return False

    return md5sum(fpath) in bad_sums


def path_for_cmd(p):
    return re.sub(r'([\'\"\s])', lambda m: r'\{}'.format(m.group()), p)

