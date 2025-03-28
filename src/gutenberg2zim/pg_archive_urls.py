#!/usr/bin/env python

# This file has been retrieved from https://github.com/gutenbergtools/libgutenberg/blob/master/pg_archive_urls.py
# and should be kept in sync manually

"""

pg_archive_urls.py

Copyright 2023 by Project Gutenberg

Distributable under the GNU General Public License Version 3 or newer.


PG uses apache rewrites and filesystem symlinks to present decent looking URLs on its
websites.
Mirror sites are updated with rsync and may not present the same urls.
This module, designed to be stand-alone, allows translation of the website urls to
mirror site urls.

Some mirror sites are not affiliated with PG, a list of morror sites is at
https://www.gutenberg.org/dirs/MIRRORS.ALL but it may or may not be up to date.

"""

import re
from urllib.parse import urlparse

# from https://github.com/gutenbergtools/ebookconverter/blob/master/ebookconverter/EbookConverter.py
FILENAMES = {
    "html.noimages": "pg{book_id}.html",
    "html.images": "pg{book_id}-images.html",
    "epub.noimages": "pg{book_id}.epub",
    "epub.images": "pg{book_id}-images.epub",
    "epub3.images": "pg{book_id}-images-3.epub",
    "kindle.noimages": "pg{book_id}.mobi",
    "kindle.images": "pg{book_id}-images.mobi",
    "kf8.images": "pg{book_id}-images-kf8.mobi",
    "pdf.noimages": "pg{book_id}.pdf",
    "pdf.images": "pg{book_id}-images.pdf",
    "txt.utf-8": "pg{book_id}.txt",
    "rdf": "pg{book_id}.rdf",
    "rst.gen": "pg{book_id}.rst",
    "cover.small": "pg{book_id}.cover.small.jpg",
    "cover.medium": "pg{book_id}.cover.medium.jpg",
    "qrcode": "pg{book_id}.qrcode.png",
    "zip": "pg{book_id}-h.zip",
}
MATCH_TYPE = re.compile(r"/ebooks/(\d+)\.([^\?\#]*)")
MATCH_DIRS = re.compile(r"/files/(\d+)/([^\?\#]*)")


# from https://github.com/gutenbergtools/libgutenberg/blob/master/libgutenberg/GutenbergGlobals.py
def archive_dir(ebook):
    """build 1/2/3/4/12345 for 12345"""
    ebook = str(ebook)
    if len(ebook) == 1:
        return "0/" + ebook
    a = []
    for c in ebook:
        a.append(c)
    a[-1] = ebook
    return "/".join(a)


def archive_url(pg_url, netloc="aleph.pglaf.org", scheme="http"):
    """translate pg canonical url to an archive url"""
    if not pg_url:
        return None
    path = urlparse(pg_url).path
    matched = MATCH_TYPE.search(path)
    if matched and matched.group(2) in FILENAMES:
        fn = FILENAMES[matched.group(2)].format(id=matched.group(1))
        return f"{scheme}://{netloc}/cache/epub/{matched.group(1)}/{fn}"
    matched = MATCH_DIRS.search(path)
    if matched:
        return f"{scheme}://{netloc}/{archive_dir(matched.group(1))}/{matched.group(2)}"
    return f"{scheme}://{netloc}{path}"


def url_for_type(pg_type, book_id, netloc="aleph.pglaf.org", scheme="http"):
    if pg_type in FILENAMES:
        fn = FILENAMES[pg_type].format(book_id=book_id)
        return f"{scheme}://{netloc}/cache/epub/{book_id}/{fn}"


# example1 = "https://www.gutenberg.org/ebooks/12345.html.images"
# example2 = "https://www.gutenberg.org/files/12345/12345-h/12345-h.htm"
# example3 = "https://www.gutenberg.org/cache/epub/12345/pg12345-images.html.utf8"
# print(archive_url(example1))
# print(archive_url(example2))
# print(archive_url(example3))
# print(url_for_type("zip", 2389))
