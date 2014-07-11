#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import tempfile
import zipfile

import requests
from path import path

from gutenberg import logger
from gutenberg.database import BookFormat, Format
from gutenberg.export import get_list_of_filtered_books, fname_for
from gutenberg.utils import (get_possible_urls_for_book,
                             download_file, FORMAT_MATRIX)


def resource_exists(url):
    r = requests.get(url, stream=True)
    return r.status_code == requests.codes.ok


def handle_zipped_epub(zippath,
                       book,
                       download_cache):

    def is_safe(fname):
        if path(fname).basename() == fname:
            return True
        return fname == os.path.join("images",
                                     path(fname).splitpath()[-1])


    zipped_files = []
    with zipfile.ZipFile(zippath, 'r') as zf:
        # check that there is no insecure data (absolute names)
        if sum([1 for n in zf.namelist()
                if not is_safe(n)]):
            return False
        else:
            zipped_files = zf.namelist()

        # create temp directory to extract to
        tmpd = tempfile.mkdtemp()
        # extract files from zip
        zf.extractall(tmpd)

    # move all extracted files to proper locations
    for fname in zipped_files:
        src = os.path.join(tmpd, fname)

        if fname.endswith('.html') or fname.endswith('.htm'):
            dst = os.path.join(download_cache,
                               "{bid}.html".format(bid=book.id))

        dst = os.path.join(download_cache,
                           "{bid}_{fname}".format(bid=book.id,
                                                  fname=fname))
        path(src).move(dst)

    # delete temp directory
    path(tmpd).rmtree_p()


def download_all_books(url_mirror, download_cache,
                       languages=[], formats=[],
                       force=False):

    available_books = get_list_of_filtered_books(languages, formats)

    for book in available_books:

        logger.info("\tDownloading content files for Book #{id}"
                    .format(id=book.id))

        # apply filters
        if not formats:
            formats = FORMAT_MATRIX.keys()

        # HTML is our base for ZIM for add it if not present
        if not 'html' in formats:
            formats.append('html')

        for format in formats:

            fpath = os.path.join(download_cache, fname_for(book, format))

            # check if already downloaded
            if path(fpath).exists() and not force:
                logger.debug("\t\t{fmt} already exists at {path}"
                             .format(fmt=format, path=fpath))
                continue

            # retrieve corresponding BookFormat
            bfs = BookFormat.filter(book=book,
                                    format=Format.get(mime=FORMAT_MATRIX.get(format)))
            if not bfs.count():
                logger.debug("[{}] not avail. for #{}# {}"
                             .format(format, book.id, book.title))
                continue

            if bfs.count() > 1:
                bf = bfs.get(images=True)
            else:
                bf = bfs.get()

            logger.debug("[{}] Requesting URLs for #{}# {}"
                         .format(format, book.id, book.title))

            # retrieve list of URLs for format unless we have it in DB
            if bf.downloaded_from and not force:
                urls = [bf.downloaded_from]
            else:
                urld = get_possible_urls_for_book(book.id)
                urls = reversed(urld.get(FORMAT_MATRIX.get(format)))

            while(urls):
                url = urls.pop()
                if not resource_exists(url):
                    continue

                # HTML files are *sometime* available as ZIP files
                if url.endswith('.zip'):
                    zpath = "{}.zip".format(fpath)
                    download_file(url, zpath)

                    # extract zipfile
                    handle_zipped_epub(zippath=zpath, book=book,
                                       download_cache=download_cache)
                else:
                    download_file(url, fpath)

                # store working URL in DB
                bf.downloaded_from = url
                bf.save()

