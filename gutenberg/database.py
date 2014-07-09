#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from peewee import (Model, SqliteDatabase,
                    CharField, DateField, BooleanField,
                    IntegerField, ForeignKeyField)

logger = logging.getLogger(__name__)

db = SqliteDatabase('gutenberg.db')
db.connect()

class License(Model):

    class Meta:
        fixtures = [
            {'slug': 'PD', 'name': ""},
            {'slug': 'None', 'name': ""},
            {'slug': 'Copyright', 'name': ""},
        ]

    slug = CharField(max_length=20, primary_key=True)
    name = CharField()


class Format(Model):

    class Meta:
        fixtures = [
            {
                'slug': 'html',
                'name': "HTML",
                'images': False,
                'pattern': "files/{id}/{id}-h.zip"
            },
            {
                'slug': 'epubi',
                'name': "ePUB with images",
                'images': True,
                'pattern': "ebooks/{id}.epub.images"
            },
            {
                'slug': 'epub',
                'name': "ePUB no images",
                'images': False,
                'pattern': "ebooks/{id}.epub.noimages"
            },
            {
                'slug': 'kindlei',
                'name': "Kindle with images",
                'images': True,
                'pattern': "ebooks/{id}.kindle.images"
            },
            {
                'slug': 'kindle',
                'name': "Kindle no images",
                'images': False,
                'pattern': "ebooks/{id}.kindle.noimages"
            },
            {
                'slug': 'text',
                'name': "Plain Text",
                'images': False,
                'pattern': "files/{id}/{id}.txt"
            },
            {
                'slug': 'textu',
                'name': "Plain Text Unicode",
                'images': False,
                'pattern': "files/{id}/{id}-0.txt"
            },
            {
                'slug': 'text8',
                'name': "Plain Text 8-bit",
                'images': False,
                'pattern': "files/{id}/{id}-8.txt"
            },
            {
                'slug': 'text5',
                'name': "Plain Text Big-5",
                'images': False,
                'pattern': "files/{id}/{id}-5.txt"
            },
            {
                'slug': 'tex',
                'name': "TeX",
                'images': False,
                'pattern': "files/{id}/{id}-t.tex"
            },
            {
                'slug': 'xml',
                'name': "XML",
                'images': False,
                'pattern': "files/{id}/{id}-x.xml"
            },
            {
                'slug': 'mp3',
                'name': "MP3",
                'images': False,
                'pattern': "files/{id}/{id}-m-###.mp3"
            },
            {
                'slug': 'rtf',
                'name': "RTF",
                'images': False,
                'pattern': "files/{id}/{id}-r.rtf"
            },
            {
                'slug': 'pdf',
                'name': "PDF",
                'images': True,
                'pattern': "files/{id}/{id}-pdf.pdf"
            },
            {
                'slug': 'lit',
                'name': "LIT",
                'images': False,
                'pattern': "files/{id}/{id}-lit.lit"
            },
            {
                'slug': 'doc',
                'name': "Word",
                'images': False,
                'pattern': "files/{id}/{id}-doc.doc"
            },
            {
                'slug': 'pdb',
                'name': "PDB",
                'images': False,
                'pattern': "files/{id}/{id}-pdb.pdb"
            },
        ]

    slug = CharField(primary_key=True)
    name = CharField(max_length=100)
    images = BooleanField(default=False)
    pattern = CharField(max_length=50)


class Author(Model):

    class Meta:
        fixtures = [
            {
                'gut_id': 'various',
                'last_name': "Various",
            },
            {
                'gut_id': '216',
                'last_name': "Anonymous",
            },
        ]

    gut_id = CharField(max_length=100)
    last_name = CharField(max_length=150)
    first_names = CharField(max_length=300)
    birth_date = DateField(null=True)
    death_date = DateField(null=True)


class Book(Model):

    id = IntegerField(primary_key=True)
    title = CharField(max_length=500)
    subtitle = CharField(max_length=500, null=True)
    author = ForeignKeyField(Author)
    date = DateField(formats='%Y-%m-%d', null=True)
    license = ForeignKeyField(License, related_name='books')
    language = CharField(max_length=10)
    downloads = IntegerField(default=0)


class BookFormat(Model):
    book = ForeignKeyField(Book)
    format = ForeignKeyField(Format)


def load_fixtures(model):
    logger.info("Loading fixtures for {}".format(model))



    for fixture in getattr(model.Meta, 'fixtures', []):
        f = model.create(**fixture)
        logger.debug("[fixtures] Created {}".format(f))


def setup_database():
    logger.info("Setting up the database")

    for model in (License, Format, Author, Book, BookFormat):
        try:
            License.create_table()
            logger.debug("Created table for {}".format(model))
        except:
            logger.debug("License table already exists.")
        else:
            load_fixtures(License)

setup_database()
