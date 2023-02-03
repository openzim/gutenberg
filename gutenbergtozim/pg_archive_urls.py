#!/usr/bin/env python

"""

pg_archive_urls.py

Copyright 2023 by Project Gutenberg

Distributable under the GNU General Public License Version 3 or newer.


PG uses apache rewrites and filesystem symlinks to present decent looking URLs on its websites.
Mirror sites are updated with rsync and may not present the same urls.
This module, designed to be stand-alone, allows translation of the website urls to mirror site urls.

Some mirror sites are not affiliated with PG, a list of morror sites is at
https://www.gutenberg.org/dirs/MIRRORS.ALL but it may or may not be up to date.

"""

import re
from urllib.parse import urlparse


# from https://github.com/gutenbergtools/ebookconverter/blob/master/ebookconverter/EbookConverter.py
FILENAMES = {
    'html.noimages':    'pg{id}.html.utf8',
    'html.images':      'pg{id}-images.html.utf8',
    'epub.noimages':    'pg{id}.epub',
    'epub.images':      'pg{id}-images.epub',
    'epub3.images':     'pg{id}-images-3.epub',
    'kindle.noimages':  'pg{id}.mobi',
    'kindle.images':    'pg{id}-images.mobi',
    'kf8.images':       'pg{id}-images-kf8.mobi',
    'pdf.noimages':     'pg{id}.pdf',
    'pdf.images':       'pg{id}-images.pdf',
    'txt.utf-8':        'pg{id}.txt.utf8',
    'rdf':              'pg{id}.rdf',
    'rst.gen':          'pg{id}.rst.utf8',
}
MATCH_TYPE = re.compile(r'/ebooks/(\d+)\.([^\?\#]*)')
MATCH_DIRS = re.compile(r'/files/(\d+)/([^\?\#]*)')

# from https://github.com/gutenbergtools/libgutenberg/blob/master/libgutenberg/GutenbergGlobals.py
def archive_dir(ebook):
    """ build 1/2/3/4/12345 for 12345 """
    ebook = str(ebook)
    if len(ebook) == 1:
        return '0/' + ebook
    a = []
    for c in ebook:
        a.append(c)
    a[-1] = ebook
    return "/".join(a)

def archive_url(pg_url, netloc="dante.pglaf.org", scheme='http'):
    """ translate pg canonical url to an archive url """
    if not pg_url:
        return None
    path = urlparse(pg_url).path
    matched = MATCH_TYPE.search(path)
    if matched and matched.group(2) in FILENAMES:
        fn = FILENAMES[matched.group(2)].format(id=matched.group(1))
        return f'{scheme}://{netloc}/cache/epub/{matched.group(1)}/{fn}'
    matched = MATCH_DIRS.search(path)
    if matched:
        return f'{scheme}://{netloc}/{archive_dir(matched.group(1))}/{matched.group(2)}'
    return f'{scheme}://{netloc}{path}'
        

# example1 = 'https://www.gutenberg.org/ebooks/12345.html.images'
# example2 = 'https://www.gutenberg.org/files/12345/12345-h/12345-h.htm'
# example3 = 'https://www.gutenberg.org/cache/epub/12345/pg12345-images.html.utf8'
# my_example_1 = 'https://www.gutenberg.org/ebooks/67735.epub3.images'
# my_example_2 = 'https://www.gutenberg.org/files/67735/67735-h/67735-h.htm'
# my_example_3 = 'https://www.gutenberg.org/files/67735/67735-h.zip'
# my_example_4 = 'https://www.gutenberg.org/cache/epub/67735/pg67735.cover.medium.jpg'
# print("example1: {} => {}".format(example1, archive_url(example1)))
# print("example2: {} => {}".format(example2, archive_url(example2)))
# print("example3: {} => {}".format(example3, archive_url(example3)))
# print("my_example_1: {} => {}".format(my_example_1, archive_url(my_example_1)))
# print("my_example_2: {} => {}".format(my_example_2, archive_url(my_example_2)))
# print("my_example_3: {} => {}".format(my_example_3, archive_url(my_example_3)))
# print("my_example_4: {} => {}".format(my_example_4, archive_url(my_example_4)))