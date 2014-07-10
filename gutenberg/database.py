#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from peewee import (Model, SqliteDatabase,
                    CharField, BooleanField,
                    IntegerField, ForeignKeyField)

from gutenberg import logger

db = SqliteDatabase('gutenberg.db')
db.connect()


class License(Model):

    class Meta:
        database = db
        fixtures = [
            {'slug': 'PD', 'name': "Copyrighted. Read the copyright notice inside this book for details."},
            {'slug': 'None', 'name': "None"},
            {'slug': 'Copyright', 'name': "Public domain in the USA."},
        ]

    slug = CharField(max_length=20, primary_key=True)
    name = CharField()

    def __unicode__(self):
        return self.name


class Format(Model):

    class Meta:
        database = db
        fixtures = [
            {
                'slug': 'html',
                'name': "HTML",
                'mime': 'text/html',
                'images': False,
                'pattern': "files/{id}/{id}-h.zip"
            },
            {
                'slug': 'epubi',
                'name': "ePUB with images",
                'mime': 'application/epub+zip',
                'images': True,
                'pattern': "ebooks/{id}.epub.images"
            },
            {
                'slug': 'epub',
                'name': "ePUB no images",
                'mime': 'application/epub+zip',
                'images': False,
                'pattern': "ebooks/{id}.epub.noimages"
            },
            {
                'slug': 'kindlei',
                'name': "Kindle with images",
                'mime': 'application/x-mobipocket-ebook',
                'images': True,
                'pattern': "ebooks/{id}.kindle.images"
            },
            {
                'slug': 'kindle',
                'name': "Kindle no images",
                'mime': 'application/x-mobipocket-ebook',
                'images': False,
                'pattern': "ebooks/{id}.kindle.noimages"
            },
            {
                'slug': 'text',
                'name': "Plain Text",
                'mime': 'text/plain',
                'images': False,
                'pattern': "files/{id}/{id}.txt"
            },
            {
                'slug': 'textu',
                'name': "Plain Text Unicode",
                'mime': 'text/plain', # two Unicode: UTF-8 and UTF-16
                'images': False,
                'pattern': "files/{id}/{id}-0.txt"
            },
            {
                'slug': 'text8',
                'name': "Plain Text 8-bit",
                'mime': 'text/plain', # six 8-bit: iso-8859-{1,2,3,7,15} and macintosh
                'images': False,
                'pattern': "files/{id}/{id}-8.txt"
            },
            {
                'slug': 'text5',
                'name': "Plain Text Big-5",
                'mime': 'text/plain; charset=big5',
                'images': False,
                'pattern': "files/{id}/{id}-5.txt"
            },
            {
                'slug': 'tex',
                'name': "TeX",
                'mime': 'application/prs.tex',
                'images': False,
                'pattern': "files/{id}/{id}-t.tex"
            },
            {
                'slug': 'xml',
                'name': "XML",
                'mime': 'text/xml',
                'images': False,
                'pattern': "files/{id}/{id}-x.xml"
            },
            {
                'slug': 'mp3',
                'name': "MP3",
                'mime': 'audio/mpeg',
                'images': False,
                'pattern': "files/{id}/{id}-m-###.mp3"
            },
            {
                'slug': 'rtf',
                'name': "RTF",
                'mime': 'text/rtf',
                'images': False,
                'pattern': "files/{id}/{id}-r.rtf"
            },
            {
                'slug': 'pdf',
                'name': "PDF",
                'mime': 'application/pdf',
                'images': True,
                'pattern': "files/{id}/{id}-pdf.pdf"
            },
            {
                'slug': 'lit',
                'name': "LIT",
                'mime': 'application/x-mslit-ebook',
                'images': False,
                'pattern': "files/{id}/{id}-lit.lit"
            },
            {
                'slug': 'doc',
                'name': "Word",
                'mime': 'application/msword',
                'images': False,
                'pattern': "files/{id}/{id}-doc.doc"
            },
            {
                'slug': 'pdb',
                'name': "PDB",
                'mime': '', # no PDB file
                'images': False,
                'pattern': "files/{id}/{id}-pdb.pdb"
            },
        ]

    slug = CharField(primary_key=True)
    name = CharField(max_length=100)
    mime = CharField(max_length=50)
    images = BooleanField(default=False)
    pattern = CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Author(Model):

    class Meta:
        database = db
        fixtures = [
            {
                'gut_id': '116',
                'last_name': "Various",
            },
            {
                'gut_id': '216',
                'last_name': "Anonymous",
            },
        ]

    gut_id = CharField(max_length=100)
    last_name = CharField(max_length=150)
    first_names = CharField(max_length=300, null=True)
    birth_year = CharField(max_length=10, null=True)
    death_year = CharField(max_length=10, null=True)

    def __unicode__(self):
        return self.name()

    def name(self):
        return "{}, {}".format(self.last_name, self.first_names)


class Book(Model):

    class Meta:
        database = db

    id = IntegerField(primary_key=True)
    title = CharField(max_length=500)
    subtitle = CharField(max_length=500, null=True)
    author = ForeignKeyField(Author)
    license = ForeignKeyField(License, related_name='books')
    language = CharField(max_length=10)
    downloads = IntegerField(default=0)

    def __unicode__(self):
        return "{}/{}".format(self.id, self.title)


class BookFormat(Model):

    class Meta:
        database = db

    book = ForeignKeyField(Book)
    format = ForeignKeyField(Format)

    def __unicode__(self):
        return "[{}] {}".format(self.format, self.book.title)


def load_fixtures(model):
    logger.info("Loading fixtures for {}".format(model._meta.name))

    for fixture in getattr(model._meta, 'fixtures', []):
        f = model.create(**fixture)
        logger.debug("[fixtures] Created {}".format(f))


def setup_database(wipe=False):
    logger.info("Setting up the database")

    for model in (License, Format, Author, Book, BookFormat):
        if wipe:
            model.drop_table(fail_silently=True)
        if not model.table_exists():
            model.create_table()
            logger.debug("Created table for {}".format(model._meta.name))
            load_fixtures(model)
        else:
            logger.debug("{} table already exists.".format(model._meta.name))
