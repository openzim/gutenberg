#!/usr/bin/env python

# The URL-translation part of this file has been retrieved from
# https://github.com/gutenbergtools/libgutenberg/blob/master/pg_archive_urls.py
# and should be kept in sync manually
# Last sync: March 29 2025 with https://github.com/gutenbergtools/libgutenberg/commit/be9866b9c2c97b41983265636bd2fa988f159faa

"""Gutenberg format resolution (moved from `gutenberg2zim.pg_archive_urls`
and `gutenberg2zim.download`).

PG uses apache rewrites and filesystem symlinks to present decent looking URLs
on its websites. Mirror sites are updated with rsync and may not present the
same urls. This module translates the website urls to mirror site urls and
exposes format resolution through the source-agnostic `FormatResolverPort`.

Some mirror sites are not affiliated with PG, a list of mirror sites is at
https://www.gutenberg.org/dirs/MIRRORS.ALL but it may or may not be up to date.
"""

import re
from urllib.parse import urlparse

from gutenberg2zim.core.models import Work
from gutenberg2zim.core.ports import DownloadRequest, FormatResolverPort

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

# map of preferred document type for every format
PG_PREFERRED_TYPES = {
    "html": ["zip", "html.images", "html.noimages"],
    "epub": ["epub3.images", "epub.images", "epub.noimages"],
    "pdf": ["pdf.images", "pdf.noimages"],
}


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


def archive_url(pg_url, mirror_url):
    """translate pg canonical url to an archive url"""
    if not pg_url:
        return None
    path = urlparse(pg_url).path
    matched = MATCH_TYPE.search(path)
    if matched and matched.group(2) in FILENAMES:
        fn = FILENAMES[matched.group(2)].format(book_id=matched.group(1))
        return f"{mirror_url}/cache/epub/{matched.group(1)}/{fn}"
    matched = MATCH_DIRS.search(path)
    if matched:
        return f"{mirror_url}/{archive_dir(matched.group(1))}/{matched.group(2)}"
    return f"{mirror_url}{path}"


def url_for_type(pg_type, book_id, mirror_url):
    if pg_type in FILENAMES:
        fn = FILENAMES[pg_type].format(book_id=book_id)
        return f"{mirror_url}/cache/epub/{book_id}/{fn}"


class GutenbergFormatResolver(FormatResolverPort):
    """`FormatResolverPort` implementation for Gutenberg mirror URLs.

    Resolution is deterministic: PG publishes every format at a well-known
    mirror URL. Because a given file may be missing on the mirror, all
    candidate URLs (in preference order) are included in
    `DownloadRequest.extra["candidate_urls"]`; the downloader probes them in
    order until one succeeds.
    """

    def __init__(self, mirror_url: str):
        self._mirror_url = mirror_url

    def resolve(self, work: Work, format_name: str) -> DownloadRequest | None:
        pg_types = PG_PREFERRED_TYPES.get(format_name)
        if not pg_types:
            return None
        candidate_urls = [
            url
            for pg_type in pg_types
            if (url := url_for_type(pg_type, work.id, self._mirror_url)) is not None
        ]
        if not candidate_urls:
            return None
        return DownloadRequest(
            url=candidate_urls[0],
            format_name=format_name,
            extra={"pg_type": pg_types[0], "candidate_urls": candidate_urls},
        )
