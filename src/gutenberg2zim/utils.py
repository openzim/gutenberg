import collections
import hashlib
import os
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

import chardet
import requests
import six
from zimscraperlib.download import save_large_file

from gutenberg2zim.constants import logger
from gutenberg2zim.database import Book, BookFormat
from gutenberg2zim.iso639 import language_name

UTF8 = "utf-8"
FORMAT_MATRIX = collections.OrderedDict(
    [
        ("html", "text/html"),
        ("epub", "application/epub+zip"),
        ("pdf", "application/pdf"),
    ]
)

BAD_BOOKS_FORMATS = {
    39765: ["pdf"],
    40194: ["pdf"],
}


NB_MAIN_LANGS = 5


def book_name_for_fs(book):
    return book.title.strip().replace("/", "-")[:230]


def article_name_for(book, *, cover=False):
    cover = "_cover" if cover else ""
    title = book_name_for_fs(book)
    return f"{title}{cover}.{book.id}.html"


def archive_name_for(book, book_format):
    return f"{book_name_for_fs(book)}.{book.id}.{book_format}"


def fname_for(book, book_format):
    return f"{book.id}.{book_format}"


def get_etag_from_url(url):
    try:
        response_headers = requests.head(  # noqa: S113
            url=url, allow_redirects=True
        ).headers
    except Exception as e:
        logger.error(url + " > Problem while head request\n" + str(e) + "\n")
        return None
    else:
        return response_headers.get("Etag", None)


def critical_error(message):
    logger.critical(f"ERROR: {message}")
    sys.exit(1)


def normalize(text=None):
    return None if text is None else unicodedata.normalize("NFC", text)


def get_project_id(languages, formats, only_books):
    parts = ["gutenberg"]
    parts.append("mul" if len(languages) > 1 else languages[0])
    if len(formats) < len(FORMAT_MATRIX):
        parts.append("-".join(formats))
    parts.append("selection" if only_books else "all")
    return "_".join(parts)


def exec_cmd(cmd):
    if isinstance(cmd, tuple | list):
        args = cmd
    else:
        args = cmd.split(" ")
    logger.debug(" ".join(args))
    return subprocess.run(args).returncode


def download_file(url, fpath):
    fpath.parent.mkdir(parents=True, exist_ok=True)
    try:
        save_large_file(url, fpath)
        return True
    except Exception as exc:
        logger.error(f"Error while downloading from {url}: {exc}")
        if fpath.exists():
            os.unlink(fpath)
        return False


def main_formats_for(book):
    fmts = [
        fmt.mime
        for fmt in BookFormat.select(BookFormat, Book)
        .join(Book)
        .switch(BookFormat)
        .where(Book.id == book.id)
    ]
    return [k for k, v in FORMAT_MATRIX.items() if v in fmts]


def get_list_of_filtered_books(languages, formats, only_books):
    if len(formats):
        qs = (
            Book.select()
            .join(BookFormat)
            .where(BookFormat.mime << [FORMAT_MATRIX.get(f) for f in formats])
            .group_by(Book.id)
        )
    else:
        qs = Book.select()

    if len(only_books):
        # print(only_books)
        qs = qs.where(Book.id << only_books)

    if len(languages) and languages[0] != "mul":
        qs = qs.where(Book.language << languages)

    return qs


def get_langs_with_count(books):
    lang_count = {}
    for book in books:
        if book.language not in lang_count:
            lang_count[book.language] = 0
        lang_count[book.language] += 1

    return [
        (language_name(lang), lang, nb)
        for lang, nb in sorted(lang_count.items(), key=lambda x: x[1], reverse=True)
    ]


def get_lang_groups(books):
    langs_wt_count = get_langs_with_count(books)
    if len(langs_wt_count) <= NB_MAIN_LANGS:
        return langs_wt_count, []
    else:
        return (
            langs_wt_count[:NB_MAIN_LANGS],
            sorted(langs_wt_count[NB_MAIN_LANGS:], key=lambda x: x[0]),
        )


def md5sum(fpath):
    return hashlib.md5(read_file(fpath)[0].encode("utf-8")).hexdigest()  # noqa: S324


def is_bad_cover(fpath):
    bad_sizes = [19263]
    bad_sums = ["a059007e7a2e86f2bf92e4070b3e5c73"]

    if Path(fpath).stat().st_size not in bad_sizes:
        return False

    return md5sum(fpath) in bad_sums


def read_file_as(fpath, encoding="utf-8"):
    # logger.debug("opening `{}` as `{}`".format(fpath, encoding))
    with open(fpath, encoding=encoding) as f:
        return f.read()


def guess_file_encoding(fpath):
    with open(fpath, "rb") as f:
        return chardet.detect(f.read()).get("encoding")


def read_file(fpath):
    for encoding in ["utf-8", "iso-8859-1"]:
        try:
            return read_file_as(fpath, encoding), encoding
        except UnicodeDecodeError:
            continue

    # common encoding failed. try with chardet
    encoding = guess_file_encoding(fpath)
    return read_file_as(fpath, encoding), encoding  # type: ignore


def save_file(content, fpath, encoding=UTF8):
    with open(fpath, "w", encoding=encoding) as f:
        f.write(content)


def zip_epub(epub_fpath, root_folder, fpaths):
    with zipfile.ZipFile(epub_fpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in fpaths:
            zf.write(Path(root_folder, fpath), fpath)


def ensure_unicode(v):
    return six.text_type(v)
