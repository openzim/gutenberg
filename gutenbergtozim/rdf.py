#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import pathlib
import re
import tarfile

import peewee
from bs4 import BeautifulSoup

from gutenbergtozim import logger
from gutenbergtozim.database import Author, Book, BookFormat, License
from gutenbergtozim.pg_archive_urls import archive_url
from gutenbergtozim.utils import (
    BAD_BOOKS_FORMATS,
    FORMAT_MATRIX,
    download_file,
    normalize,
)


def get_rdf_fpath():
    fname = "rdf-files.tar.bz2"
    fpath = pathlib.Path(fname).resolve()
    return fpath


def download_rdf_file(rdf_path, rdf_url):
    """Download rdf-files archive"""
    if rdf_path.exists():
        logger.info("\trdf-files archive already exists in {}".format(rdf_path))
        return

    logger.info("\tDownloading {} into {}".format(rdf_url, rdf_path))
    download_file(rdf_url, rdf_path)


def parse_and_fill(rdf_path, only_books=[], force=False):
    logger.info("\tLooping throught RDF files in {}".format(rdf_path))

    rdf_tarfile = tarfile.open(name=rdf_path, mode="r|bz2")

    for rdf_member in rdf_tarfile:

        rdf_member_path = pathlib.Path(rdf_member.name)

        # skip books outside of requested list
        if only_books and int(rdf_member_path.stem.replace("pg", "").replace(".rdf", "")) not in only_books:
            continue

        if rdf_member_path.name == "pg0.rdf":
            continue

        if not str(rdf_member_path.name).endswith(".rdf"):
            continue

        parse_and_process_file(rdf_tarfile, rdf_member, force)


def parse_and_process_file(rdf_tarfile, rdf_member, force=False):

    gid = re.match(r".*/pg([0-9]+).rdf", rdf_member.name).groups()[0]

    if Book.get_or_none(id=int(gid)):
        logger.info(
            "\tSkipping already parsed file {} for book id {}".format(
                rdf_member.name, gid
            )
        )
        return

    logger.info("\tParsing file {} for book id {}".format(rdf_member.name, gid))
    parser = RdfParser(rdf_tarfile.extractfile(rdf_member).read(), gid).parse()

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
        files = soup.find_all("pgterms:file")
        self.files = []
        for x in files:
            self.files.append({
                "mime": x.find("rdf:value").text,
                "url": x.attrs["rdf:about"],
                "pattern": x.attrs["rdf:about"].split("/")[-1],
            })
            
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
        file
        for file in parser.files
        if file["mime"].startswith("application/pdf")
    ]:
        parser.files.append({
            "pattern": "{id}-pdf.pdf",
            "mime": "application/pdf",
            "url": "forced",
            }
        )

    # Insert formats
    for file in parser.files:

        # Sanitize MIME
        mime = file["mime"]
        if not mime.startswith("text/plain"):
            mime = re.sub(r"; charset=[a-z0-9-]+", "", mime)
        # else:
        #    charset = re.match(r'; charset=([a-z0-9-]+)', mime).groups()[0]

        # Insert format type
        pattern = re.sub(r"" + parser.gid, "{id}", file["pattern"])
        pattern = pattern.split("/")[-1]

        bid = int(book_record.id)

        if bid in BAD_BOOKS_FORMATS.keys() and mime in [
            FORMAT_MATRIX.get(f) for f in BAD_BOOKS_FORMATS.get(bid)
        ]:
            logger.error(
                "\t**** EXCLUDING **** {} for book #{} from list.".format(mime, bid)
            )
            continue

        # Insert book format
        BookFormat.create(
            book=book_record,
            mime=mime,
            images=pattern.endswith(".images")
            or mime == "application/pdf",
            pattern=pattern,
            rdf_url=file["url"],
            archive_url=archive_url(file["url"]),
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
