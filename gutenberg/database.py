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

    mime = CharField(max_length=100)
    images = BooleanField(default=True)
    pattern = CharField(max_length=100)

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
