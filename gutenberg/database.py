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
            {'slug': 'PD', 'name': "Public domain in the USA."},
            {'slug': 'None', 'name': "None"},
            {'slug': 'Copyright', 'name': "Copyrighted. Read the copyright notice inside this book for details."},
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
        return self.mime


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

    gut_id = CharField(primary_key=True, max_length=100)
    last_name = CharField(max_length=150)
    first_names = CharField(max_length=300, null=True)
    birth_year = CharField(max_length=10, null=True)
    death_year = CharField(max_length=10, null=True)

    def __unicode__(self):
        return self.name()

    def name(self):
        if not self.first_names and not self.last_name:
            return "Anonymous"

        if not self.first_names:
            return self.last_name

        if not self.last_name:
            return self.first_names

        return "{f} {l}".format(l=self.last_name, f=self.first_names)

    def to_dict(self):
        return {'label': self.name(),
                'id': self.gut_id,
                'last_name': self.last_name,
                'first_names': self.first_names,
                'birth_year': self.birth_year,
                'death_year': self.death_year}

    def to_array(self):
        return [
            self.name(),
            self.gut_id,
            # self.last_name,
            # self.first_names,
            # self.birth_year,
            # self.death_year,
        ]


class Book(Model):

    class Meta:
        database = db

    id = IntegerField(primary_key=True)
    title = CharField(max_length=500)
    subtitle = CharField(max_length=500, null=True)
    author = ForeignKeyField(Author, related_name='books')
    license = ForeignKeyField(License, related_name='books')
    language = CharField(max_length=10)
    downloads = IntegerField(default=0)

    def __unicode__(self):
        return "{}/{}".format(self.id, self.title)

    def to_dict(self):
        return {'title': self.title,
                'subtitle': self.subtitle,
                'author': self.author.name(),
                'license': self.license,
                'language': self.language,
                'downloads': self.downloads}

    def to_array(self):
        return [
            self.title,
            # self.subtitle,
            self.author.name(),
            # self.license,
            # self.language,
            # self.downloads
        ]


class BookFormat(Model):

    class Meta:
        database = db

    book = ForeignKeyField(Book, related_name='bookformats')
    format = ForeignKeyField(Format, related_name='bookformats')
    downloaded_from = CharField(max_length=300, null=True)

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
