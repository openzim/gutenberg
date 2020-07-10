#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import re
import pathlib
from multiprocessing.dummy import Pool

import peewee
from path import Path as path
from bs4 import BeautifulSoup

from gutenbergtozim import logger
from gutenbergtozim.utils import exec_cmd, download_file
from gutenbergtozim.database import Author, Format, BookFormat, License, Book
from gutenbergtozim.utils import BAD_BOOKS_FORMATS, FORMAT_MATRIX, normalize


def setup_rdf_folder(rdf_url, rdf_path, force=False):
    """ Download and Extract rdf-files """

    rdf_tarball = download_rdf_file(rdf_url)
    extract_rdf_files(rdf_tarball, rdf_path, force=force)


def download_rdf_file(rdf_url):
    fname = "rdf-files.tar.bz2"

    if path(fname).exists():
        logger.info("\tdf-files.tar.bz2 already exists in {}".format(fname))
        return fname

    logger.info("\tDownloading {} into {}".format(rdf_url, fname))
    download_file(rdf_url, pathlib.Path(fname).resolve())

    return fname


def extract_rdf_files(rdf_tarball, rdf_path, force=False):
    if path(rdf_path).exists() and not force:
        logger.info("\tRDF-files folder already exists in {}".format(rdf_path))
        return

    logger.info("\tExtracting {} into {}".format(rdf_tarball, rdf_path))

    # create destdir if not exists
    dest = path(rdf_path)
    dest.mkdir_p()

    exec_cmd(
        [
            "tar",
            "-C",
            rdf_path,
            "--strip-components",
            "2",
            "--extract",
            "--no-same-owner",
            "--no-same-permissions",
            "-f",
            rdf_tarball,
        ]
    )
    return


def parse_and_fill(rdf_path, concurrency, only_books=[], force=False):
    logger.info("\tLooping throught RDF files in {}".format(rdf_path))

    fpaths = []
    for root, dirs, files in os.walk(rdf_path):
        if root.endswith("999999"):
            continue

        # skip books outside of requsted list
        if len(only_books) and path(root).basename() not in [
            str(bid) for bid in only_books
        ]:
            continue

        for fname in files:
            if fname in (".", "..", "pg0.rdf"):
                continue

            if not fname.endswith(".rdf"):
                continue

            fpaths.append(os.path.join(root, fname))

    fpaths = sorted(
        fpaths, key=lambda f: int(re.match(r".*/pg([0-9]+).rdf", f).groups()[0])
    )

    def ppf(x):
        return parse_and_process_file(x, force)

    Pool(concurrency).map(ppf, fpaths)


def parse_and_process_file(rdf_file, force=False):
    if not path(rdf_file).exists():
        raise ValueError(rdf_file)

    gid = re.match(r".*/pg([0-9]+).rdf", rdf_file).groups()[0]

    if Book.get_or_none(id=int(gid)):
        logger.info("\tSkipping already parsed file {}".format(rdf_file))
        return

    logger.info("\tParsing file {}".format(rdf_file))
    with open(rdf_file, "r", encoding="UTF-8") as f:
        parser = RdfParser(f.read(), gid).parse()

    if parser.license == "None":
        logger.info("\tWARN: Unusable book without any information {}".format(gid))
    elif parser.title == "":
        logger.info("\tWARN: Unusable book without title {}".format(gid))
    else:
        save_rdf_in_database(parser)


class RdfParser:
    def __init__(self, rdf_data, gid):
        self.rdf_data = rdf_data
        self.gid = gid

        self.author_id = None
        self.author_name = None
        self.first_name = None
        self.last_name = None

        self.bookshelf = None
        self.cover_image = 0

    def parse(self):
        soup = BeautifulSoup(self.rdf_data, "lxml")

        # The tile of the book: this may or may not be divided
        # into a new-line-seperated title and subtitle.
        # If it is, then we will just split the title.
        self.title = soup.find("dcterms:title")
        self.title = self.title.text if self.title else "- No Title -"
        self.title = self.title.split("\n")[0]
        self.subtitle = " ".join(self.title.split("\n")[1:])
        self.author_id = None

        # Parsing for the bookshelf name
        self.bookshelf = soup.find("pgterms:bookshelf")
        if self.bookshelf:
            self.bookshelf = self.bookshelf.find("rdf:value").text

        # Search rdf to see if the image exists at the hard link
        # https://www.gutenberg.ord/cache/epub/id/pg{id}.cover.medium.jpg
        if soup.find("cover.medium.jpg"):
            self.cover_image = 1

        # Parsing the name of the Author. Sometimes it's the name of
        # an organization or the name is not known and therefore
        # the <dcterms:creator> or <marcrel:com> node only return
        # "anonymous" or "unknown". For the case that it's only one word
        # `self.last_name` will be null.
        # Because of a rare edge case that the field of the parsed
        # author's name
        # has more than one comma we will join the first name in reverse,
        # starting
        # with the second item.
        self.author = soup.find("dcterms:creator") or soup.find("marcrel:com")
        if self.author:
            self.author_id = self.author.find("pgterms:agent")
            self.author_id = (
                self.author_id.attrs["rdf:about"].split("/")[-1]
                if "rdf:about" in getattr(self.author_id, "attrs", "")
                else None
            )

            if self.author.find("pgterms:name"):
                self.author_name = self.author.find("pgterms:name")
                self.author_name = self.author_name.text.split(",")

                if len(self.author_name) > 1:
                    self.first_name = " ".join(self.author_name[::-2]).strip()
                self.last_name = self.author_name[0]

        # Parsing the birth and (death, if the case) year of the author.
        # These values are likely to be null.
        self.birth_year = soup.find("pgterms:birthdate")
        self.birth_year = self.birth_year.text if self.birth_year else None
        self.birth_year = get_formatted_number(self.birth_year)

        self.death_year = soup.find("pgterms:deathdate")
        self.death_year = self.death_year.text if self.death_year else None
        self.death_year = get_formatted_number(self.death_year)

        # ISO 639-3 language codes that consist of 2 or 3 letters
        self.language = soup.find("dcterms:language").find("rdf:value").text

        # The download count of the books on www.gutenberg.org.
        # This will be used to determine the popularity of the book.
        self.downloads = soup.find("pgterms:downloads").text

        # The book might be licensed under GPL, public domain
        # or might be copyrighted
        self.license = soup.find("dcterms:rights").text

        # Finding out all the file types this book is available in
        file_types = soup.find_all("pgterms:file")
        self.file_types = {}
        for x in file_types:
            if not x.find("rdf:value").text.endswith("application/zip"):
                k = x.attrs["rdf:about"].split("/")[-1]
                v = x.find("rdf:value").text
                self.file_types.update({k: v})

        return self


def save_rdf_in_database(parser):

    # Insert author, if it not exists
    if parser.author_id:
        try:
            author_record = Author.get(gut_id=parser.author_id)
        except Exception:
            try:
                author_record = Author.create(
                    gut_id=parser.author_id,
                    last_name=normalize(parser.last_name),
                    first_names=normalize(parser.first_name),
                    birth_year=parser.birth_year,
                    death_year=parser.death_year,
                )
            # concurrent workers might colide here so we retry once on IntegrityError
            except peewee.IntegrityError:
                author_record = Author.get(gut_id=parser.author_id)
        else:
            if parser.last_name:
                author_record.last_name = normalize(parser.last_name)
            if parser.first_name:
                author_record.first_names = normalize(parser.first_name)
            if parser.birth_year:
                author_record.birth_year = parser.birth_year
            if parser.death_year:
                author_record.death_year = parser.death_year
            author_record.save()
    else:
        # No author, set Anonymous
        author_record = Author.get(gut_id="216")

    # Get license
    try:
        license_record = License.get(name=parser.license)
    except Exception:
        license_record = None

    # Insert book

    try:
        book_record = Book.get(id=parser.gid)
    except Book.DoesNotExist:
        book_record = Book.create(
            id=parser.gid,
            title=normalize(parser.title.strip()),
            subtitle=normalize(parser.subtitle.strip()),
            author=author_record,  # foreign key
            license=license_record,  # foreign key
            language=parser.language.strip(),
            downloads=parser.downloads,
            bookshelf=parser.bookshelf,
            cover_page=parser.cover_image,
        )
    else:
        book_record.title = normalize(parser.title.strip())
        book_record.subtitle = normalize(parser.subtitle.strip())
        book_record.author = author_record  # foreign key
        book_record.license = license_record  # foreign key
        book_record.language = parser.language.strip()
        book_record.downloads = parser.downloads
        book_record.save()

    # insert pdf if not exists in parser.file_types
    # this is done as presence of PDF on server and RDF is inconsistent
    if not [
        key
        for key in parser.file_types
        if parser.file_types[key].startswith("application/pdf")
    ]:
        parser.file_types.update({"{id}-pdf.pdf": "application/pdf"})

    # Insert formats
    for file_type in parser.file_types:

        # Sanitize MIME
        mime = parser.file_types[file_type]
        if not mime.startswith("text/plain"):
            mime = re.sub(r"; charset=[a-z0-9-]+", "", mime)
        # else:
        #    charset = re.match(r'; charset=([a-z0-9-]+)', mime).groups()[0]

        # Insert format type
        pattern = re.sub(r"" + parser.gid, "{id}", file_type)
        pattern = pattern.split("/")[-1]

        bid = int(book_record.id)

        if bid in BAD_BOOKS_FORMATS.keys() and mime in [
            FORMAT_MATRIX.get(f) for f in BAD_BOOKS_FORMATS.get(bid)
        ]:
            logger.error(
                "\t**** EXCLUDING **** {} for book #{} from list.".format(mime, bid)
            )
            continue

        format_record, _ = Format.get_or_create(
            mime=mime,
            images=file_type.endswith(".images")
            or parser.file_types[file_type] == "application/pdf",
            pattern=pattern,
        )

        # Insert book format
        BookFormat.get_or_create(
            book=book_record, format=format_record  # foreign key  # foreign key
        )


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
    if all(["-" in num, num.replace("-", "").strip().isdigit()]):
        return " ".join([num, "BC"])
    return num


if __name__ == "__main__":
    # Bacic Test with a sample rdf file
    nums = ["{0:0=5d}".format(i) for i in range(21000, 40000)]
    for num in nums:
        print(num)
        curd = os.path.dirname(os.path.realpath(__file__))
        rdf = os.path.join(curd, "..", "rdf-files", num, "pg" + num + ".rdf")
        if os.path.isfile(rdf):
            data = ""
            with open(rdf, "r") as f:
                data = f.read()

            parser = RdfParser(data, num).parse()
            print(parser.first_name, parser.last_name)
