#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os

import envoy

from gutenberg import logger

from gutenberg.export import get_list_of_filtered_books


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
    base = 'http://zimfarm.kiwix.org/gutenberg/'

    def __init__(self):
        pass

    def build(self):
        if self.id > 10:
            base_url = os.path.join(
                os.path.join(*list(str(self.id))[:-1]), str(self.id))
            base_url = os.path.join(self.base, base_url)
            urls = [os.path.join(base_url, x) for x in self.file_types]
        else:
            logger.warning('Figuring out the url of books \
                with an ID of {ID <= 10} is not implemented yet')
            return None

        return urls

    def with_base(self, base):
        self.base = base

    def with_id(self, id):
        self.id = id

    def with_files(self, file_types):
        self.file_types = file_types

    def __unicode__(self):
        return self.build_url()


def download_all_books(url_mirror, download_cache,
                       languages=[], formats=[]):

    available_books = get_list_of_filtered_books(languages, formats)

    for b in available_books:
        book = Book.get(id=b.id)
        filtered_book = [bf.format for bf in
                         BookFormat.select().where(BookFormat.book == book)]

        allowed_mime = ''
        if formats:
            allowed_mime = [formats[x] for x in formats if x in FORMAT_MATRIX]
        else:
            allowed_mime = FORMAT_MATRIX.values()

        f = lambda x: x.mime.split(';')[0].strip()
        available_formats = [{x.pattern.format(id=b.id): {'mime': f(x), 'id': b.id}}
                             for x in filtered_book if f(x) in allowed_mime]
        # print(available_formats)
        # files = filter_out_file_types(available_formats)
        # build_urls(files)

        break
    return


def filter_out_file_types(files):
    count = defaultdict(list)
    for f in files:
        for k, v in f.items():
            count[v['mime']].append({'name': k, 'id': v['id']})

    for k, v in count.items():
        index = index_of_substring(v, '.images')
        if index:
            count[k] = v[index]
        else:
            if len(v) > 1:
                index = index_of_substring(v, '.noimages')
                if index:
                    count[k] = v[index]
            else:
                count[k] = v[0]
        if len(v) > 1:
            count[k] = v[0]
    return dict(count)


def index_of_substring(lst, substring):
    for i, s in enumerate(lst):
        if substring in s['name']:
            return i
    return False


def build_urls(files):
    for k, v in files.items():
        print('')
        print(v)
        print(v['name'])


if __name__ == '__main__':
    b = UrlBuilder()
    b.with_id(1234)
    b.with_files([u'1234.kindle.noimages', u'1234-8.txt', u'1234.kindle.images',
                  u'1234-h.zip', u'1234.epub.images', u'1234.epub.noimages'])
    print('Url of the book: ' + str(b.build()))
