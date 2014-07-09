#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os

from path import path

from gutenberg import logger
from gutenberg.utils import exec_cmd

from bs4 import BeautifulSoup
import requests


def setup_rdf_folder(rdf_url, rdf_path):
    """ Download and Extract rdf-files """

    rdf_tarball = download_rdf_file(rdf_url)
    extract_rdf_files(rdf_tarball, rdf_path)


def download_rdf_file(rdf_url):
    fname = 'rdf-files.tar.bz2'

    if path(fname).exists():
        logger.info("\rdf-files.tar.bz2 already exists in {}".format(fname))
        return fname

    logger.info("\tDownloading {} into {}".format(rdf_url, fname))

    cmd = "wget -O {fname} -c {url}".format(fname=fname, url=rdf_url)
    exec_cmd(cmd)

    return fname


def extract_rdf_files(rdf_tarball, rdf_path):
    if path(rdf_path).exists():
        logger.info("\tRDF files already exists in {}".format(rdf_path))
        return

    logger.info("\tExtracting {} into {}".format(rdf_tarball, rdf_path))

    # create destdir if not exists
    dest = path(rdf_path)
    dest.mkdir()

    cmd = "tar -C {dest} --strip-components 2 -x -f {tarb}".format(
        dest=rdf_path, tarb=rdf_tarball)
    exec_cmd(cmd)
    return


def parse_and_fill(rdf_path):
    logger.info("\tLooping throught RDF files in {}".format(rdf_path))

    for root, dirs, files in os.walk(rdf_path):
        if root.endswith('999999'):
            continue

        for fname in files:
            if fname in ('.', '..'):
                continue

            if not fname.endswith('.rdf'):
                continue

            fpath = os.path.join(root, fname)
            parse_and_process_file(fpath)


def parse_and_process_file(rdf_file):
    logger.info("\tParsing file {}".format(rdf_file))
    if not path(rdf_file).exists():
        raise ValueError(rdf_file)


class RdfParser():

    def __init__(self, html):
        self.html = html

    def parse(self):
        soup = BeautifulSoup(self.html)

        # Parsing the name. Sometimes it's the name of
        # an organization or the name is not known and therefore
        # the <dcterms:creator> or <marcrel:com> node only return
        # "anonymous" or "unknown". For the case that it's only one word
        # `self.laste_name` will be null.
        # Because of a rare edge case that the fild of the parsed author's name
        # has more than one comma we will join the first name in reverse, starting
        # with the second item.
        self.first_name = ''
        self.last_name = ''
        self.author = soup.find('dcterms:creator')
        if not self.author:
            self.author = soup.find('marcrel:com')
        self.author = self.author.find('pgterms:name').text
        self.author_name = self.author.split(',')
        self.first_name = ''.join(self.author.split(',')[::-1])
        self.last_name = self.author.split(',')[0]

        # Parsing the birth and (death, if the case) year of the author.
        # These values are likely to be null.
        self.birth_year = soup.find('pgterms:birthhdate')
        self.birth_year = self.birth_year.text if self.birth_year else None
        self.birth_year = get_formatted_number(self.birth_year)

        self.death_year = soup.find('pgterms:deathhdate')
        self.death_year = self.death_year.text if self.death_year else None
        self.death_year = get_formatted_number(self.death_year)

        # ISO 639-1 language codes that consist of 2 letters
        self.language = soup.find('dcterms:language').find('rdf:value').text

        # The download count of the books on www.gutenberg.org.
        # This will be used to determine the popularity of the book.
        self.downloads = soup.find('pgterms:downloads').text

        # The book might be licensed under GPL, public domain
        # or might be copyrighted
        self.license = soup.find('dcterms:rights').text

        # Finding out all the file types this book is available in
        file_types = soup.find_all('pgterms:file')
        self.file_types = map(lambda x: x.attrs['rdf:about'], file_types)

        return self


def get_formatted_number(num):
    """
    Get a formatted string of a number from a not-predictable-string 
    that may or may not actually contain a number.
    Append a BC notation to the number num with, if the
    number is negative.
    returns: a formatted string of the number, or num if
             num is not negative or None.
    """
    if not num:
        return None
    if all(['-' in num, num.replace('-', '').strip().isdigit()]):
        return ' '.join([num, 'BC'])
    return num


if __name__ == '__main__':
    # Bacic Test with a sample rdf file
    import os
    curd = os.path.abspath(__file__)

    if os.path.isfile(curd):
        data = ''
        with open('pg45213.rdf', 'r') as f:
            data = f.read()

        parser = RdfParser(data).parse()
        print(vars(parser))
