import hashlib
import subprocess
import unicodedata
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import NoReturn, Protocol

import chardet

from gutenberg2zim.constants import logger
from gutenberg2zim.core.language import language_name
from gutenberg2zim.core.models import Creator, Work
from gutenberg2zim.core.work_store import WorkStore

UTF8 = "utf-8"
ALL_FORMATS = ["epub", "pdf", "html"]

NB_MAIN_LANGS = 5


class WorkNamingInfo(Protocol):
    """What the ZIM path-naming helpers need from a work (duck-typed)"""

    title: str
    id: str


def book_name_for_fs(work: WorkNamingInfo) -> str:
    return work.title.strip().replace("/", "-")[:230]


def article_name_for(work: WorkNamingInfo, *, cover: bool = False) -> str:
    cover_suffix = "_cover" if cover else ""
    title = book_name_for_fs(work)
    return f"{title}{cover_suffix}.{work.id}"


def archive_name_for(work: WorkNamingInfo, book_format: str) -> str:
    return f"{book_name_for_fs(work)}.{work.id}.{book_format}"


def fname_for(work: WorkNamingInfo, book_format: str) -> str:
    return f"{work.id}.{book_format}"


def requested_formats(work: Work, all_requested_formats: list[str]) -> list[str]:
    """Requested formats minus the ones that turned out unsupported"""
    unsupported = work.extra.get("unsupported_formats", [])
    return [fmt for fmt in all_requested_formats if fmt not in unsupported]


def work_lcc_shelf(work: Work) -> str | None:
    """Id of the work's first collection (its classification shelf), if any"""
    return work.collections[0].id if work.collections else None


def primary_creator(work: Work) -> Creator:
    """First creator of the work, with an Anonymous fallback when none"""
    if work.creators:
        return work.creators[0]
    # Reserved non-numeric id: cannot collide with a real source creator id
    # (Gutenberg's own Anonymous, id 216, is assigned by its metadata layer)
    return Creator(id="anonymous", name="Anonymous", sort_name="Anonymous")


def work_creators(work: Work) -> list[Creator]:
    """The work's creators, with the Anonymous fallback when it has none"""
    return work.creators or [primary_creator(work)]


def creator_birth_year(creator: Creator) -> str | None:
    """Raw birth year string of a creator, if known"""
    raw = creator.extra.get("birth_year_raw")
    if raw is not None:
        return str(raw)
    return str(creator.birth_date) if creator.birth_date is not None else None


def creator_death_year(creator: Creator) -> str | None:
    """Raw death year string of a creator, if known"""
    raw = creator.extra.get("death_year_raw")
    if raw is not None:
        return str(raw)
    return str(creator.death_date) if creator.death_date is not None else None


def creator_template_context(creator: Creator) -> SimpleNamespace:
    """Template-friendly view of a Creator"""
    return SimpleNamespace(
        id=creator.id,
        name=creator.name,
        first_names=creator.extra.get("first_names"),
        last_name=creator.sort_name,
        birth_year=creator_birth_year(creator),
        death_year=creator_death_year(creator),
    )


def work_template_context(work: Work) -> SimpleNamespace:
    """Template-friendly view of a Work for the Jinja templates"""
    return SimpleNamespace(
        id=work.id,
        title=work.title,
        subtitle=work.subtitle,
        languages=work.languages,
        license=work.license,
        downloads=work.extra.get("downloads", 0),
        lcc_shelf=work_lcc_shelf(work),
        has_cover=work.extra.get("has_cover", work.cover is not None),
        description=work.description,
        author=creator_template_context(primary_creator(work)),
        requested_formats=lambda formats: requested_formats(work, formats),
    )


class CriticalError(RuntimeError):
    """Raised on fatal errors that should abort the scraper"""


def critical_error(message) -> NoReturn:
    logger.critical(f"ERROR: {message}")
    raise CriticalError(message)


def normalize(text: str | None = None) -> str | None:
    return None if text is None else unicodedata.normalize("NFC", text)


def get_zim_name(languages, formats, is_selection, prefix: str):
    parts = [prefix]
    parts.append("mul" if len(languages) > 1 else languages[0])
    if len(formats) < len(ALL_FORMATS):
        parts.append("-".join(formats))
    parts.append("selection" if is_selection else "all")
    return "_".join(parts)


def exec_cmd(cmd):
    if isinstance(cmd, tuple | list):
        args = cmd
    else:
        args = cmd.split(" ")
    logger.debug(" ".join(args))
    return subprocess.run(args, check=False).returncode


def get_langs_with_count(
    languages: list[str] | None, work_store: WorkStore
) -> list[tuple[str, str, int]]:
    """Get language counts with their names from the work store"""
    lang_count = {}

    for work in work_store.works:
        for code in work.languages:
            # if not appear in user request languages list, skip counting
            if languages and code not in languages:
                continue
            if code not in lang_count:
                lang_count[code] = 0
            lang_count[code] += 1

    return [
        (language_name(lang), lang, nb)
        for lang, nb in sorted(lang_count.items(), key=lambda x: x[1], reverse=True)
    ]


def get_lang_groups(
    work_store: WorkStore,
) -> tuple[list[tuple[str, str, int]], list[tuple[str, str, int]]]:
    """Split languages into main and other groups from the work store"""
    langs_wt_count = get_langs_with_count(None, work_store)
    if len(langs_wt_count) <= NB_MAIN_LANGS:
        return langs_wt_count, []
    else:
        return (
            langs_wt_count[:NB_MAIN_LANGS],
            sorted(langs_wt_count[NB_MAIN_LANGS:], key=lambda x: x[0] or ""),
        )


def md5sum(fpath: Path) -> str:
    return hashlib.md5(fpath.read_bytes()).hexdigest()  # noqa: S324


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
    try:
        return read_file_as(fpath, "utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    encoding = guess_file_encoding(fpath)
    if not encoding:
        encoding = "iso-8859-1"
    return read_file_as(fpath, encoding), encoding


def save_file(content, fpath, encoding=UTF8):
    with open(fpath, "w", encoding=encoding) as f:
        f.write(content)


def zip_epub(epub_fpath: Path, root_folder: Path, fpaths: list[str]) -> None:
    if "mimetype" not in fpaths:
        raise ValueError("EPUB is missing its mimetype file")

    with zipfile.ZipFile(epub_fpath, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write mimetype first, uncompressed, per EPUB spec
        zf.write(root_folder / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for fpath in fpaths:
            if fpath == "mimetype":
                continue
            zf.write(root_folder / fpath, fpath)


def ensure_unicode(v):
    return str(v)
