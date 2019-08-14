#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import tempfile
import zipfile
from pprint import pprint as pp
from multiprocessing.dummy import Pool

import requests
from path import Path as path

from gutenbergtozim import logger, TMP_FOLDER
from gutenbergtozim.urls import get_urls
from gutenbergtozim.database import BookFormat, Format
from gutenbergtozim.export import get_list_of_filtered_books, fname_for
from gutenbergtozim.utils import download_file, FORMAT_MATRIX, ensure_unicode


def resource_exists(url):
    r = requests.get(url, stream=True, timeout=20)  # in seconds
    return r.status_code == requests.codes.ok


def handle_zipped_epub(zippath,
                       book,
                       download_cache):

    def clfn(fn):
        return os.path.join(*os.path.split(fn)[1:])

    def is_safe(fname):
        fname = ensure_unicode(clfn(fname))
        if path(fname).basename() == fname:
            return True
        return fname == os.path.join("images",
                                     path(fname).splitpath()[-1])

    zipped_files = []
    # create temp directory to extract to
    tmpd = tempfile.mkdtemp(dir=TMP_FOLDER)
    try:
        with zipfile.ZipFile(zippath, 'r') as zf:
            # check that there is no insecure data (absolute names)
            if sum([1 for n in zf.namelist()
                    if not is_safe(ensure_unicode(n))]):
                path(tmpd).rmtree_p()
                return False
            else:
                # zipped_files = [clfn(fn) for fn in zf.namelist()]
                zipped_files = zf.namelist()

            # extract files from zip
            zf.extractall(tmpd)
    except zipfile.BadZipfile:
        # file is not a zip file when it should be.
        # don't process it anymore as we don't know what to do.
        # could this be due to an incorrect/incomplete download?
        return

    # is there multiple HTML files in ZIP ? (rare)
    mhtml = sum([1 for f in zipped_files
                 if f.endswith('html') or f.endswith('.htm')]) > 1
    # move all extracted files to proper locations
    for fname in zipped_files:
        # skip folders
        if not path(fname).ext:
            continue

        src = os.path.join(tmpd, fname)
        if os.path.exists(src):
            fname = path(fname).basename()

            if fname.endswith('.html') or fname.endswith('.htm'):
                if mhtml:
                    if fname.startswith("{}-h.".format(book.id)):
                        dst = os.path.join(download_cache,
                                           "{bid}.html".format(bid=book.id))
                    else:
                        dst = os.path.join(download_cache,
                                           "{bid}_{fname}".format(bid=book.id,
                                                                  fname=fname))
                else:
                    dst = os.path.join(download_cache,
                                       "{bid}.html".format(bid=book.id))
            else:
                dst = os.path.join(download_cache,
                                   "{bid}_{fname}".format(bid=book.id,
                                                          fname=fname))
            try:
                path(src).move(dst)
            except Exception as e:
                import traceback
                print(e)
                print("".join(traceback.format_exc()))
                raise
                # import ipdb; ipdb.set_trace()

    # delete temp directory
    path(tmpd).rmtree_p()


def download_book(book, download_cache, languages, formats, force):
    logger.info("\tDownloading content files for Book #{id}"
                .format(id=book.id))

    # apply filters
    if not formats:
        formats = FORMAT_MATRIX.keys()

    # HTML is our base for ZIM for add it if not present
    if 'html' not in formats:
        formats.append('html')

    for format in formats:

        fpath = os.path.join(download_cache, fname_for(book, format))

        # check if already downloaded
        if path(fpath).exists() and not force:
            logger.debug("\t\t{fmt} already exists at {path}"
                         .format(fmt=format, path=fpath))
            continue

        # retrieve corresponding BookFormat
        bfs = BookFormat.filter(book=book)

        if format == 'html':
            patterns = ['mnsrb10h.htm', '8ledo10h.htm', 'tycho10f.htm',
                        '8ledo10h.zip', 'salme10h.htm', '8nszr10h.htm',
                        '{id}-h.html', '{id}.html.gen', '{id}-h.htm',
                        '8regr10h.zip', '{id}.html.noimages',
                        '8lgme10h.htm', 'tycho10h.htm', 'tycho10h.zip',
                        '8lgme10h.zip', '8indn10h.zip', '8resp10h.zip',
                        '20004-h.htm', '8indn10h.htm', '8memo10h.zip',
                        'fondu10h.zip', '{id}-h.zip', '8mort10h.zip']
            bfso = bfs
            bfs = bfs.join(Format).filter(Format.pattern << patterns)
            if not bfs.count():
                pp(list([
                    (b.format.mime, b.format.images, b.format.pattern)
                    for b in bfs]))
                pp(list([
                    (b.format.mime, b.format.images, b.format.pattern)
                    for b in bfso]))
                logger.error("html not found")
                continue
        else:
            bfs = bfs.filter(BookFormat.format << Format.filter(
                mime=FORMAT_MATRIX.get(format)))

        if not bfs.count():
            logger.debug("[{}] not avail. for #{}# {}"
                         .format(format, book.id, book.title).encode("utf-8"))
            continue

        if bfs.count() > 1:
            try:
                bf = bfs.join(Format).filter(Format.images).get()
            except Exception:
                bf = bfs.get()
        else:
            bf = bfs.get()

        logger.debug("[{}] Requesting URLs for #{}# {}"
                     .format(format, book.id, book.title).encode("utf-8"))

        # retrieve list of URLs for format unless we have it in DB
        if bf.downloaded_from and not force:
            urls = [bf.downloaded_from]
        else:
            urld = get_urls(book)
            urls = list(reversed(urld.get(FORMAT_MATRIX.get(format))))

        import copy
        allurls = copy.copy(urls)

        while(urls):
            url = urls.pop()

            if len(allurls) != 1:
                if not resource_exists(url):
                    continue

            # HTML files are *sometime* available as ZIP files
            if url.endswith('.zip'):
                zpath = "{}.zip".format(fpath)

                if not download_file(url, zpath):
                    logger.error("ZIP file donwload failed: {}"
                                 .format(zpath))
                    continue

                # extract zipfile
                handle_zipped_epub(zippath=zpath, book=book,
                                   download_cache=download_cache)
            else:
                if not download_file(url, fpath):
                    logger.error("file donwload failed: {}".format(fpath))
                    continue

            # store working URL in DB
            bf.downloaded_from = url
            bf.save()

        if not bf.downloaded_from:
            logger.error("NO FILE FOR #{}/{}".format(book.id, format))
            pp(allurls)
            continue


def download_all_books(download_cache, concurrency,
                       languages=[], formats=[],
                       only_books=[], force=False):
    available_books = get_list_of_filtered_books(
        languages=languages,
        formats=formats,
        only_books=only_books)

    # ensure dir exist
    path(download_cache).mkdir_p()

    def dlb(b):
        return download_book(b, download_cache, languages, formats, force)
    Pool(concurrency).map(dlb, available_books)
