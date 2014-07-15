#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import hashlib
from contextlib import contextmanager
from collections import defaultdict

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
    # logger.debug("** {}".format(cmd))
    return envoy.run(str(cmd.encode('utf-8')))


def download_file(url, fname):
    output = "--output {}".format(fname) if fname else "--remote-name"
    cmd = ("curl --fail --insecure --location {output} --silent "
           "--show-error -C - --url {url}".format(output=output, url=url))
    # logger.debug("--/ {}".format(cmd))
    cmdr = exec_cmd(cmd)
    return cmdr.status_code == 0


class UrlBuilder:

    """
    Url builder for the files of a Gutenberg book.
    Example:
        >>> builder = UrlBuilder()
        >>> builder.with_id(<some_id>)
        >>> builder.with_base(UrlBuilder.BASE_{ONE|TWO|THREE})
        >>> url = builder.build()
    """
    BASE_ONE = 'http://gutenberg.readingroo.ms/'
    BASE_TWO = 'http://gutenberg.readingroo.ms/cache/generated/'
    BASE_THREE = 'http://gutenberg.readingroo.ms/etext'

    def __init__(self):
        self.base = self.BASE_ONE

    def build(self):
        """
        Build either an url depending on whether the base url
        is `BASE_ONE` or `BASE_TWO`.
        The former generates urls according to the Url pattern:
            id: 10023 -> pattern: <base-url>/1/0/0/2/10023
        The latter generates urls according to the Url pattern:
            id: 10023 -> pattern: <base-url>/10023
        There's no implementation for the book Id's 0-10, because
        these books do not exist.

        """
        if self.b_id > 10:
            if self.base == self.BASE_ONE:
                base_url = os.path.join(
                    os.path.join(*list(str(self.b_id))[:-1]), str(self.b_id))
                url = os.path.join(self.base, base_url)
            elif self.base == self.BASE_TWO:
                url = os.path.join(self.base, str(self.b_id))
            elif self.base == self.BASE_THREE:
                url = self.base

        else:
            logger.warning('Figuring out the url of books \
                with an ID of {ID <= 10} is not implemented')
            return None

        return url

    def with_base(self, base):
        self.base = base

    def with_id(self, b_id):
        self.b_id = b_id

    def __unicode__(self):
        return self.build_url()


def get_possible_urls_for_book(book):
    """
    Get all possible urls that could point to the
    book on either of the two mirrors.
    param: book: The book you want the possible urls from
    returns: a list of all possible urls sorted by their probability
    """
    filtered_book = [bf.format for bf in
                     BookFormat.select().where(BookFormat.book == book)]

    # Strip out the encoding of the file
    f = lambda x: x.mime.split(';')[0].strip()
    available_formats = [{x.pattern.format(id=book.id): {'mime': f(x), 'id': book.id}}
                         for x in filtered_book
                         if f(x) in FORMAT_MATRIX.values()]
    files = sort_by_mime_type(available_formats)
    return build_urls(files)


def sort_by_mime_type(files):
    """
    Reverse the passed in `files` dict and return a dict
    that is sorted by `{mimetype: {filetype, id}}` instead of
    by `{filetype: mimetype}`.
    """
    mime = defaultdict(list)
    for f in files:
        for k, v in f.items():
            mime[v['mime']].append({'name': k, 'id': v['id']})
    return dict(mime)


def build_urls(files):
    mapping = {
        'application/epub+zip': build_epub,
        'application/pdf': build_pdf,
        'text/html': build_html
    }

    for i in mapping:
        if i in files:
            files[i] = mapping[i](files[i])

    return files


def build_epub(files):
    """
    Build the posssible urls of the epub file.
    """
    urls = []
    b_id = str(files[0]['id'])
    u = UrlBuilder()
    u.with_id(b_id)
    u.with_base(UrlBuilder.BASE_TWO)

    if not u.build():
        return []

    name = ''.join(['pg', b_id])
    url = os.path.join(u.build(), name + '.epub')
    urls.append(url)
    return urls


def build_pdf(files):
    """
    Build the posssible urls of the pdf files.
    """
    urls = []
    b_id = str(files[0]['id'])
    u = UrlBuilder()
    u.with_base(UrlBuilder.BASE_TWO)
    u.with_id(b_id)

    if not u.build():
        return []

    for i in files:
        if not 'images' in i['name']:
            url = os.path.join(u.build(), i['name'])
            urls.append(url)

    url_dash = os.path.join(u.build(), b_id + '-' + 'pdf' + '.pdf')
    url_normal = os.path.join(u.build(), b_id + '.pdf')
    url_pg = os.path.join(u.build(), 'pg' + b_id + '.pdf')

    urls.extend([url_dash, url_normal, url_pg])
    return list(set(urls))


def build_html(files):
    """
    Build the posssible urls of the html files.
    """
    urls = []
    b_id = str(files[0]['id'])
    file_names = [i['name'] for i in files]
    u = UrlBuilder()
    u.with_id(i['id'])

    if not u.build():
        return []

    if all([not '-h.html' in file_names, '-h.zip' in file_names]):
        for i in files:
            url = os.path.join(u.build(), i['name'])
            urls.append(url)

    url_zip = os.path.join(u.build(), b_id + '-h' + '.zip')
    # url_utf8 = os.path.join(u.build(), b_id + '-8' + '.zip')
    url_html = os.path.join(u.build(), b_id + '-h' + '.html')
    url_htm = os.path.join(u.build(), b_id + '-h' + '.htm')

    u.with_base(UrlBuilder.BASE_TWO)
    name = ''.join(['pg', b_id])
    html_utf8 = os.path.join(u.build(), name + '.html.utf8')

    u.with_base(UrlBuilder.BASE_THREE)
    file_index = index_of_substring(files, ['html', 'htm'])
    file_name = files[file_index]['name']
    etext_nums = []
    etext_nums.extend(range(90, 100))
    etext_nums.extend(range(0, 6))
    etext_names = ["{0:0=2d}".format(i) for i in etext_nums]
    etext_urls = []
    for i in etext_names:
        etext_urls.append(os.path.join(u.build() + i, file_name))

    urls.extend([url_zip, url_htm, url_html, html_utf8])
    urls.extend(etext_urls)
    return list(set(urls))


def index_of_substring(lst, substrings):
    for i, s in enumerate(lst):
        for substring in substrings:
            if substring in s:
                return i
    return -1


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

if __name__ == '__main__':
    book = Book.get(id=1339)
    print(get_possible_urls_for_book(book))
