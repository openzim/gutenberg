#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import json

from path import path
from bs4 import BeautifulSoup
from jinja2 import Template

from gutenberg import logger
from gutenberg.utils import FORMAT_MATRIX
from gutenberg.database import Book, Format, BookFormat, Author


def get_list_of_filtered_books(languages, formats):
    qs = Book.select()

    if len(languages):
        qs = qs.where(Book.language << languages)

    if len(formats):
        qs = qs.join(BookFormat) \
               .where(Format.mime << [FORMAT_MATRIX.get(f) for f in formats])

    return qs


def export_all_books(static_folder,
                     download_cache,
                     languages=[],
                     formats=[]):

    # ensure dir exist
    path(static_folder).mkdir_p()

    books = get_list_of_filtered_books(languages, formats)

    # export to HTML
    for book in books:
        export_book_to(book=book,
                       static_folder=static_folder,
                       download_cache=download_cache)

    # export to JSON helpers
    export_to_json_helpers(books=books,
                           static_folder=static_folder,
                           languages=languages,
                           formats=formats)


def article_name_for(book, cover=False):
    cover = "_cover" if cover else ""
    return "{title}{cover}.html".format(title=book.title, cover=cover)


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
    logger.info("\tExporting Book #{id}.")

    # actual book content, as HTML
    article_fpath = os.path.join(static_folder, article_name_for(book))
    logger.info("\t\tExporting to {}".format(article_fpath))
    html = html_content_for(book=book,
                            static_folder=static_folder,
                            download_cache=download_cache)
    new_html = update_html_for_static(book=book, html_content=html)
    with open(article_fpath, 'w') as f:
        f.write(new_html)

    # book presentation article
    cover_fpath = os.path.join(static_folder,
                                 article_name_for(book=book, cover=True))
    logger.info("\t\tExporting to {}".format(cover_fpath))
    html = cover_html_content_for(book=book)
    with open(cover_fpath, 'w') as f:
        f.write(html)


def export_to_json_helpers(books, static_folder, languages, formats):

    def dumpjs(col, fn):
        with open(os.path.join(static_folder, fn), 'w') as f:
            json.dump(col, f)

    # all books sorted by popularity
    dumpjs([book.to_dict()
            for book in books.order_by(Book.downloads.desc())],
           'full_by_popularity.json')

    # all books sorted by title
    dumpjs([book.to_dict()
            for book in books.order_by(Book.title.asc())],
           'full_by_title.json')

    # language-specific collections
    for lang in languages:
        # by popularity
        dumpjs([book.to_dict()
                for book in books.where(Book.language == lang)
                                 .order_by(Book.downloads.desc())],
                'lang_{}_by_popularity.json'.format(lang))
        # by title
        dumpjs([book.to_dict()
                for book in books.where(Book.language == lang)
                                 .order_by(Book.title.asc())],
                'lang_{}_by_popularity.json'.format(lang))

    # author specific collections
    authors = Author.select().where(
        Author.gut_id << list(set([book.author.gut_id
                                   for book in books])))
    for author in authors:
        # by popularity
        dumpjs([book.to_dict()
                for book in books.where(Book.author == author)
                                 .order_by(Book.downloads.desc())],
                'auth_{}_by_popularity.json'.format(author.gut_id))
        # by title
        dumpjs([book.to_dict()
                for book in books.where(Book.author == author)
                                 .order_by(Book.title.asc())],
                'auth_{}_by_popularity.json'.format(author.gut_id))

    # authors list sorted by name
    dumpjs([author.to_dict()
            for author in authors.order_by(Author.last_name.asc(),
                                           Author.first_names.asc())],
                'authors.json')

    # languages list sorted by code
    avail_langs = list(set([b.language for b in books]))
    dumpjs(sorted(avail_langs), 'languages.json')
