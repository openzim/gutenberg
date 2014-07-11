#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from collections import defaultdict

from gutenberg import logger
from gutenberg.export import get_list_of_filtered_books
from gutenberg.utils import UrlBuilder, FORMAT_MATRIX
from gutenberg.database import *


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
        print(available_formats)
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
        print ('')
        print (v)
        print (v['name'])
