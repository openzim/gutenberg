#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os

from collections import defaultdict

import envoy

from gutenberg import logger
from gutenberg.database import Book, BookFormat, Format


FORMAT_MATRIX = {
    'epub': 'application/epub+zip',
    'pdf': 'application/pdf',
    'html': 'text/html'
}


def exec_cmd(cmd):
    return envoy.run(str(cmd))


def download_file(url, fname):
    output = "--output {}".format(fname) if fname else "--remote-name"
    cmd = ("curl --fail --insecure --location {output} --silent "
           "--show-error -C - --url {url}".format(output=output, url=url))
    cmdr = exec_cmd(cmd)
    return cmdr.status_code == 0


class UrlBuilder:

    """
    Url builder for the files of a Gutenberg book.
    """
    BASE_ONE = 'http://zimfarm.kiwix.org/gutenberg/'
    BASE_TWO = 'http://zimfarm.kiwix.org/gutenberg-generated/'

    def __init__(self):
        self.base = self.BASE_ONE

    def build(self):
        if self.id > 10:
            if self.base == self.BASE_ONE:
                base_url = os.path.join(
                    os.path.join(*list(str(self.id))[:-1]), str(self.id))
                url = os.path.join(self.base, base_url)
            elif self.base == self.BASE_TWO:
                url = os.path.join(self.base, str(self.id))

        else:
            logger.warning('Figuring out the url of books \
                with an ID of {ID <= 10} is not implemented yet')
            return None

        return url

    def get_base_one_links():
        pass

    def with_base(self, base):
        self.base = base

    def with_id(self, id):
        self.id = id

    def __unicode__(self):
        return self.build_url()


def get_possible_urls_for_book(book):
    formats = []

    filtered_book = [bf.format for bf in
                     BookFormat.select().where(BookFormat.book == book)]

    f = lambda x: x.mime.split(';')[0].strip()
    available_formats = [{x.pattern.format(id=id): {'mime': f(x), 'id': id}}
                         for x in filtered_book]
    files = sort_by_mime_type(available_formats)
    return build_urls(files)


def sort_by_mime_type(files):
    count = defaultdict(list)
    for f in files:
        for k, v in f.items():
            count[v['mime']].append({'name': k, 'id': v['id']})
    return dict(count)


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
    urls = []
    id = str(files[0]['id'])
    u = UrlBuilder()
    u.with_id(files[0]['id'])
    u.with_base(UrlBuilder.BASE_TWO)
    name = ''.join(['pg', id])
    url = os.path.join(u.build(), name + '.epub')
    urls.append(url)
    return urls


def build_pdf(files):
    urls = []
    id = str(files[0]['id'])
    u = UrlBuilder()
    u.with_id(files[0]['id'])
    for i in files:
        if not 'images' in i['name']:
            url = os.path.join(u.build(), i['name'])
            urls.append(url)
    url_dash = os.path.join(u.build(), id + '-' + 'pdf' + '.pdf')
    url_normal = os.path.join(u.build(), id + '.pdf')
    urls.extend([url_dash, url_normal])
    return list(set(urls))


def build_html(files):
    urls = []
    id = str(files[0]['id'])
    file_names = [i['name'] for i in files]
    u = UrlBuilder()
    u.with_id(i['id'])

    if all([not '-h.html' in file_names, '-h.zip' in file_names]):
        for i in files:
            url = os.path.join(u.build(), i['name'])
            urls.append(url)

    url_zip = os.path.join(u.build(), id + '-h' + '.zip')
    url_html = os.path.join(u.build(), id + '-h' + '.html')
    url_htm = os.path.join(u.build(), id + '-h' + '.htm')
    urls.extend([url_zip, url_htm, url_html])
    return list(set(urls))


def main_formats_for(book):
    fmts = [fmt.format.mime
            for fmt in BookFormat.select(BookFormat, Book, Format)
                                 .join(Book).switch(BookFormat)
                                 .join(Format)
                                 .where(Book.id == book.id)]
    return [k for k, v in FORMAT_MATRIX.items() if v in fmts]


def get_list_of_filtered_books(languages, formats):

    if len(formats):
        qs = Book.select().join(BookFormat) \
                 .join(Format) \
                 .where(Format.mime << [FORMAT_MATRIX.get(f)
                                        for f in formats]).group_by(Book.id)
    else:
        qs = Book.select()

    if len(languages):
        qs = qs.where(Book.language << languages)

    return qs


if __name__ == '__main__':
    b = UrlBuilder()
    b.with_id(1234)
    print('Url of the book: ' + str(b.build()))
