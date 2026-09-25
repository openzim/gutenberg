"""Author details enrichment for Gutenberg works (bio + portrait).

When the `--with-author-details` option is enabled, the Gutenberg pipeline
enriches every author with a short biography and a portrait sourced from
Wikipedia.

The pivot from a Gutenberg author id to its Wikipedia article is the
`pgterms:webpage` link that Project Gutenberg curates inside the author
`pgterms:agent` block of the per-book RDF (see `sources.gutenberg.metadata`).
A single call to the Wikipedia REST summary endpoint yields both the
biography intro (`extract`) and the portrait thumbnail URL. This avoids any
ambiguous-name matching and keeps the number of Wikipedia requests to at
most one per author.

We use the Wikipedia REST summary endpoint (page/summary) rather than the
MediaWiki Action API because it is the endpoint designed for this exact need:
it returns the article's plain-text intro and, when relevant, the portrait
thumbnail in a single well-defined JSON response, without the parse/query
boilerplate (templates, revisions, prop selection) the Action API requires.

Author biographies are only fetched from the English Wikipedia for now: the
REST summary URL is hard-coded to `en.wikipedia.org`, so authors whose
`pgterms:webpage` points to another language (or to a non-Wikipedia page) are
silently skipped until multi-language support is added.

Authors without a Wikipedia link are left untouched, so a scrape never
depends on Wikipedia being reachable.
"""

import json
import re
import urllib.parse
from dataclasses import replace
from threading import Lock

import requests

from gutenberg2zim.constants import logger
from gutenberg2zim.core.concurrency import parallel_map
from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.models import Creator
from gutenberg2zim.core.rewriters.image_rewriter import ImageProcessor
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler

WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

PORTRAIT_PATH_TEMPLATE = "authors/{id}.webp"


def wikipedia_title(creator: Creator) -> str | None:
    """Extract the Wikipedia article title from a creator's webpage link."""
    webpage = creator.extra.get("webpage_resource")
    if not webpage:
        return None
    match = re.match(r"https?://en\.wikipedia\.org/wiki/(.+)", webpage)
    if not match:
        return None
    return urllib.parse.unquote(match.group(1))


def fetch_author_summary(engine: DownloadEngine, title: str) -> dict | None:
    """Return the Wikipedia REST summary JSON for `title`, or None on failure."""
    url = WIKIPEDIA_SUMMARY_URL.format(title=urllib.parse.quote(title, safe="()"))
    try:
        response = engine.fetch_bytes(url)
    except requests.RequestException as exc:
        logger.warning(f"Failed to fetch Wikipedia summary for {title}: {exc}")
        return None
    try:
        summary = json.loads(response)
    except ValueError:
        logger.warning(f"Invalid JSON in Wikipedia summary for {title}")
        return None
    if "extract" not in summary:
        return None
    return summary


def enrich_creator(
    creator: Creator,
    engine: DownloadEngine,
    assembler: ZimAssembler,
) -> Creator:
    """Return `creator` enriched with bio and portrait when available."""
    title = wikipedia_title(creator)
    if not title:
        return creator
    summary = fetch_author_summary(engine, title)
    if summary is None:
        return creator

    extra = dict(creator.extra)
    extract = summary.get("extract")
    if isinstance(extract, str) and extract.strip():
        extra["bio"] = extract

    image = summary.get("thumbnail") or summary.get("originalimage")
    source = image.get("source") if image else None
    if isinstance(source, str) and source:
        portrait_path = PORTRAIT_PATH_TEMPLATE.format(id=creator.id)
        try:
            data = engine.fetch_bytes(source)
            # Wikipedia serves a raster thumbnail; store it as WebP like covers
            data = ImageProcessor.optimize_image_content(data)
            assembler.add_item_for(
                path=portrait_path,
                content=data,
                mimetype="image/webp",
                is_front=False,
            )
            extra["portrait_path"] = portrait_path
        except (requests.RequestException, OSError, ValueError) as exc:
            logger.warning(
                f"Failed to fetch or store portrait for {creator.name}: {exc}"
            )

    return replace(creator, extra=extra) if extra != dict(creator.extra) else creator


def enrich_authors(
    store: WorkStore,
    engine: DownloadEngine,
    assembler: ZimAssembler,
    *,
    concurrency: int,
) -> None:
    """Fetch bio and portrait for every author that has a Wikipedia page."""
    works = list(store.works)
    unique: dict[str, Creator] = {}
    for work in works:
        for creator in work.creators:
            unique.setdefault(creator.id, creator)

    creators = list(unique.values())
    logger.info(f"Enriching {len(creators)} author(s) from Wikipedia")

    results: dict[str, Creator] = {}
    results_lock = Lock()

    def enrich_entry(creator: Creator) -> None:
        enriched = enrich_creator(creator, engine, assembler)
        with results_lock:
            results[creator.id] = enriched

    parallel_map(enrich_entry, creators, concurrency)

    for work in works:
        work.creators = [results.get(creator.id, creator) for creator in work.creators]
