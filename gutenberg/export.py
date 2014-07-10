#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os

from path import path
from bs4 import BeautifulSoup
from jinja2 import Template

from gutenberg import logger
from gutenberg.utils import FORMAT_MATRIX
from gutenberg.database import Book, Format, BookFormat


def export_all_books(static_folder,
                     download_cache,
                     languages=[],
                     formats=[]):

    qs = Book.select()

    if len(languages):
        qs = qs.where(Book.language << languages)

    if len(formats):
        qs = qs.join(BookFormat) \
               .where(Format.mime << [FORMAT_MATRIX.get(f) for f in formats])

    # export to HTML
    for book in qs:
        logger.info(book)
        export_book_to(book=book,
                       static_folder=static_folder,
                       download_cache=download_cache)


def article_name_for(book, cover=False):
    return book.title


def fname_for(book, format):
    return "{book.id}.{format}"


def html_content_for(book, static_folder, download_cache):

    html_fpath = os.path.join(download_cache, fname_for(book, 'html'))

    # is HTML file present?
    if not path(html_fpath).exist():
        raise ValueError("Missing HTML content for #{} at {}"
                         .format(book.id, html_fpath))

    with open(html_fpath, 'r') as f:
        return f.read()


def update_html_for_static(book, html_content):
    # update all <img> links from images/xxx.xxx to {id}_xxx.xxx
    soup = BeautifulSoup(html_content)
    for img in soup.findAll('img'):
        img.attrs['href'] = img.attrs['href'].replace('images/', '{id}_'.format(book.id))
    return soup.text


def cover_html_content_for(book):
    cover_img = path("{id}_cover.jpg")
    cover_img = str(cover_img) if cover_img.exists() else None
    context = {
        'book': book,
        'cover_img': cover_img,
        'formats': [k for k, v in FORMAT_MATRIX.items()
                    if BookFormat.select().where(Book.id == book.id)
                                          .where(Format.mime == v)]
    }
    with open(os.path.join('templates', 'cover_article.html'), 'r') as tmpl:
        template = Template(tmpl.read())
    return template.render(**context)


def export_book_to(book, static_folder, download_cache):

    # actual book content, as HTML
    article_fpath = os.path.join(static_folder, article_name_for(book))
    html = html_content_for(book=book,
                            static_folder=static_folder,
                            download_cache=download_cache)
    new_html = update_html_for_static(book=book, html_content=html)
    with open(article_fpath, 'w') as f:
        f.write(new_html)

    # book presentation article
    cover_fpath = os.path.join(static_folder,
                                 article_name_for(book=book, cover=True))
    html = cover_html_content_for(book=book)
    with open(cover_fpath, 'w') as f:
        f.write(html)
