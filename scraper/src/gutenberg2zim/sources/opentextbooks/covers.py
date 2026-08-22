"""Cover extraction for Open Textbook Library downloads.

The OTL API does not provide cover-image URLs. Covers are therefore derived
from the downloaded source file: the first PDF page or the EPUB package's
declared cover image.
"""

import io
import zipfile
from pathlib import PurePosixPath
from typing import Protocol
from urllib.parse import unquote, urldefrag, urljoin

import pymupdf
from bs4 import BeautifulSoup
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from gutenberg2zim.constants import logger
from gutenberg2zim.core.rewriters.image_rewriter import ImageProcessor


class CoverFetchEngine(Protocol):
    """Minimal download interface required to fetch a page cover."""

    def fetch_bytes(self, url: str) -> bytes: ...


def extract_cover(content: bytes, format_name: str) -> bytes | None:
    """Extract and WebP-encode a cover image from a downloaded book file."""
    try:
        if format_name == "pdf":
            image = _pdf_first_page(content)
        elif format_name == "epub":
            image = _epub_cover(content)
        else:
            return None
        return ImageProcessor.optimize_image_content(image) if image else None
    except Exception as exc:
        logger.debug("Could not extract %s cover: %s", format_name, exc)
        return None


def fetch_page_cover(engine: CoverFetchEngine, source_url: str | None) -> bytes | None:
    """Fetch the cover advertised by an OTL book page and encode it as WebP."""
    if not source_url:
        return None
    try:
        page_url = f"{source_url.rstrip('/')}.html"
        soup = BeautifulSoup(engine.fetch_bytes(page_url), "html.parser")
        # OTL's og:image is a landscape social-media card. The page cover is
        # the portrait book image shown to readers, so always prefer it.
        cover = soup.find("img", class_="cover")
        image_url = cover.get("src") if cover else None
        if not image_url:
            image = soup.find("meta", property="og:image")
            image_url = image.get("content") if image else None
        if not image_url:
            return None
        if not isinstance(image_url, str):
            return None
        return ImageProcessor.optimize_image_content(
            engine.fetch_bytes(urljoin(page_url, image_url))
        )
    except Exception as exc:
        logger.debug("Could not fetch OTL page cover for %s: %s", source_url, exc)
        return None


def _pdf_first_page(content: bytes) -> bytes | None:
    document = pymupdf.open(stream=content, filetype="pdf")
    try:
        if document.page_count == 0:
            return None
        pixmap = document[0].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
        return pixmap.tobytes("png")
    finally:
        document.close()


def _epub_cover(content: bytes) -> bytes | None:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        container = etree.fromstring(archive.read("META-INF/container.xml"), parser)
        rootfile = container.find(".//{*}rootfile")
        if rootfile is None or not (opf_path := rootfile.get("full-path")):
            return None

        package = etree.fromstring(archive.read(opf_path), parser)
        manifest = {
            item.get("id"): item
            for item in package.findall(".//{*}manifest/{*}item")
            if item.get("id") and item.get("href")
        }
        cover_id = next(
            (
                meta.get("content")
                for meta in package.findall(".//{*}metadata/{*}meta")
                if meta.get("name") == "cover" and meta.get("content")
            ),
            None,
        )
        cover_item = manifest.get(cover_id) if cover_id else None
        if cover_item is None:
            cover_item = next(
                (
                    item
                    for item in manifest.values()
                    if "cover-image" in item.get("properties", "").split()
                ),
                None,
            )
        if cover_item is None:
            cover_item = next(
                (
                    item
                    for item in manifest.values()
                    if item.get("media-type", "").startswith("image/")
                ),
                None,
            )
        if cover_item is None:
            return None

        href = unquote(urldefrag(cover_item.attrib["href"])[0])
        cover_path = PurePosixPath(opf_path).parent / href
        return archive.read(str(cover_path))
