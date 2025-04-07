import hashlib
import subprocess
import sys
import unicodedata
import zipfile
from functools import reduce
from pathlib import Path

import chardet
import requests
import six
from zimscraperlib.download import save_large_file

from gutenberg2zim.constants import logger
from gutenberg2zim.database import Book
from gutenberg2zim.iso639 import language_name

UTF8 = "utf-8"
ALL_FORMATS = ["epub", "pdf", "html"]

NB_MAIN_LANGS = 5


def book_name_for_fs(book: Book) -> str:
    return book.title.strip().replace("/", "-")[:230]  # type: ignore


def article_name_for(book: Book, *, cover: bool = False) -> str:
    cover_suffix = "_cover" if cover else ""
    title = book_name_for_fs(book)
    return f"{title}{cover_suffix}.{book.book_id}.html"


def archive_name_for(book: Book, book_format: str) -> str:
    return f"{book_name_for_fs(book)}.{book.book_id}.{book_format}"


def fname_for(book: Book, book_format: str) -> str:
    return f"{book.book_id}.{book_format}"


def get_etag_from_url(url: str) -> str | None:
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


def normalize(text: str | None = None) -> str | None:
    return None if text is None else unicodedata.normalize("NFC", text)


def get_project_id(languages, formats, only_books):
    parts = ["gutenberg"]
    parts.append("mul" if len(languages) > 1 else languages[0])
    if len(formats) < len(ALL_FORMATS):
        parts.append("-".join(formats))
    parts.append("selection" if only_books else "all")
    return "_".join(parts)


def exec_cmd(cmd):
    if isinstance(cmd, tuple | list):
        args = cmd
    else:
        args = cmd.split(" ")
    logger.debug(" ".join(args))
    return subprocess.run(args, check=False).returncode


def download_file(url: str, fpath: Path) -> bool:
    fpath.parent.mkdir(parents=True, exist_ok=True)
    try:
        save_large_file(url, fpath)
        return True
    except Exception as exc:
        logger.error(f"Error while downloading from {url}: {exc}")
        fpath.unlink(missing_ok=True)
        return False


def get_list_of_filtered_books(languages, formats, only_books):
    qs = Book.select()

    if len(formats):
        qs = qs.where(
            Book.unsupported_formats.is_null(True)
            | reduce(
                lambda x, y: x | y,
                [
                    ~Book.unsupported_formats.contains(book_format)
                    for book_format in formats
                ],
            )
        )

    if len(only_books):
        qs = qs.where(Book.book_id << only_books)

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
            sorted(langs_wt_count[NB_MAIN_LANGS:], key=lambda x: x[0] or ""),
        )


def md5sum(fpath):
    return hashlib.md5(read_file(fpath)[0].encode("utf-8")).hexdigest()  # noqa: S324


def is_bad_cover(fpath: Path) -> bool:
    bad_sizes = [19263]
    bad_sums = ["a059007e7a2e86f2bf92e4070b3e5c73"]

    if fpath.stat().st_size not in bad_sizes:
        return False

    return md5sum(fpath) in bad_sums


def read_file_as(fpath: Path, encoding="utf-8") -> str:
    # logger.debug("opening `{}` as `{}`".format(fpath, encoding))
    with open(fpath, encoding=encoding) as f:
        return f.read()


def guess_file_encoding(fpath: Path) -> str | None:
    with open(fpath, "rb") as f:
        return chardet.detect(f.read()).get("encoding")


def read_file(fpath: Path):
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


def zip_epub(epub_fpath: Path, root_folder: Path, fpaths: list[str]) -> None:
    with zipfile.ZipFile(epub_fpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in fpaths:
            zf.write(root_folder / fpath, fpath)


def ensure_unicode(v):
    return six.text_type(v)
