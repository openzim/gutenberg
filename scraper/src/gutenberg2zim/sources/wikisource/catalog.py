"""OPDS-backed Wikisource discovery.

ws-export (https://ws-export.wmcloud.org) publishes, per Wikisource language, an
OPDS Atom feed of the books flagged "ready for export". Each feed lives under
``/opds/<lang>/`` with a language-specific filename, so discovery reads the
directory index to find the feed(s), then parses their ``<entry>`` elements.

Every entry is self-contained: it carries the title, author, language, license,
year, source page and one ready-made ws-export download link per format. So a
`WorkRef` here already holds everything the metadata port needs - no per-book
fetch, unlike Open Textbook Library.
"""

import hashlib
import re
import unicodedata
from collections.abc import Iterable
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup, Tag

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.ports import CatalogFilters, CatalogPort, WorkRef
from gutenberg2zim.core.utils import critical_error

WIKISOURCE_SOURCE = "wikisource"
BASE_URL = "https://ws-export.wmcloud.org"

# OPDS acquisition media type -> the format name used across the pipeline.
FORMAT_BY_MEDIA_TYPE = {
    "application/epub+zip": "epub",
    "application/x-mobipocket-ebook": "mobi",
    "application/xhtml+xml": "xhtml",
}

ACQUISITION_REL = "http://opds-spec.org/acquisition"


def slugify(text: str) -> str:
    """ASCII, lowercase, hyphen-separated slug (empty for non-latin scripts)."""
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:80]


def work_id(lang: str, page: str) -> str:
    """A path-safe id, unique per (language, page), readable where possible.

    `page` is the ws-export page name (percent-encoded, as it appears in the
    source URL); the short digest guarantees uniqueness when slugs collide or
    the title is non-latin and slugifies to nothing.
    """
    slug = slugify(unquote(page))
    digest = hashlib.sha256(f"{lang}:{page}".encode()).hexdigest()[:8]
    return f"{lang}_{slug}-{digest}" if slug else f"{lang}_{digest}"


class WikisourceCatalog(CatalogPort):
    """Discover Wikisource books from ws-export's per-language OPDS feeds."""

    def __init__(
        self,
        engine: DownloadEngine,
        base_url: str = BASE_URL,
        **_: object,
    ):
        self._engine = engine
        self._base_url = base_url.rstrip("/")

    def discover(self, filters: CatalogFilters) -> Iterable[WorkRef]:
        languages = [lang.lower() for lang in (filters.languages or [])]
        if not languages:
            critical_error(
                "Wikisource is organised per language; pass one or more codes "
                "via --languages (e.g. --languages=en,fr)."
            )

        requested = set(filters.formats) if filters.formats else None
        refs: list[WorkRef] = []
        for lang in languages:
            refs.extend(self._discover_language(lang, requested))

        selected = self._select_positions(refs, filters.book_ids)
        logger.info(
            "  Selected %s Wikisource books from %s catalog entries (languages: %s)",
            len(selected),
            len(refs),
            ", ".join(languages),
        )
        return selected

    def _discover_language(
        self, lang: str, requested: set[str] | None
    ) -> list[WorkRef]:
        refs: list[WorkRef] = []
        for feed_url in self._feed_urls(lang):
            feed = BeautifulSoup(self._engine.fetch_bytes(feed_url), "xml")
            for entry in feed.find_all("entry"):
                if not isinstance(entry, Tag):
                    continue
                extra = self._parse_entry(entry, lang)
                if extra is None:
                    continue
                advertised = {name for name, _mt, _url in extra["formats"]}
                if requested is not None and not (requested & advertised):
                    continue
                refs.append(
                    WorkRef(
                        id=work_id(lang, extra["page"]),
                        source=WIKISOURCE_SOURCE,
                        extra=extra,
                    )
                )
        return refs

    def _feed_urls(self, lang: str) -> list[str]:
        index_url = f"{self._base_url}/opds/{lang}/"
        try:
            index = self._engine.fetch_bytes(index_url).decode("utf-8", "replace")
        except requests.RequestException as exc:
            logger.warning(
                "No Wikisource OPDS index for language %r, skipping (%s)", lang, exc
            )
            return []
        soup = BeautifulSoup(index, "html.parser")
        feed_urls = [
            urljoin(index_url, href)
            for anchor in soup.find_all("a", href=True)
            if isinstance(anchor, Tag)
            and (href := str(anchor["href"])).lower().endswith(".xml")
        ]
        if not feed_urls:
            logger.warning("No OPDS feed found under %s", index_url)
        return feed_urls

    @staticmethod
    def _parse_entry(entry: Tag, lang: str) -> dict | None:
        source = _text(entry, "source") or _text(entry, "id")
        title = _text(entry, "title")
        if not source or not title:
            return None
        page = source.rsplit("/wiki/", 1)[-1]

        formats: list[tuple[str, str, str]] = []
        for link in entry.find_all("link"):
            if not isinstance(link, Tag) or link.get("rel") != ACQUISITION_REL:
                continue
            media_type = str(link.get("type") or "")
            href = link.get("href")
            if not href:
                continue
            name = FORMAT_BY_MEDIA_TYPE.get(media_type, media_type)
            formats.append((name, media_type, str(href)))
        if not formats:
            return None

        author = entry.find("author")
        return {
            "title": title,
            "author": _text(author, "name") if isinstance(author, Tag) else None,
            "language": _text(entry, "language") or lang,
            "license": _text(entry, "rights"),
            "source_url": source,
            "issued": _text(entry, "issued"),
            "page": page,
            "lang": lang,
            "formats": formats,
        }

    @staticmethod
    def _select_positions(
        refs: list[WorkRef], book_ids: list[str] | None
    ) -> list[WorkRef]:
        if not book_ids:
            return refs
        positions = set()
        for book_id in book_ids:
            try:
                positions.add(int(book_id))
            except ValueError:
                continue
        if not positions:
            return refs
        return [
            ref for position, ref in enumerate(refs, start=1) if position in positions
        ]


def _text(parent: Tag | None, name: str) -> str | None:
    if parent is None:
        return None
    tag = parent.find(name)
    if not isinstance(tag, Tag):
        return None
    text = tag.get_text(strip=True)
    return text or None
