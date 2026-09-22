"""Cover discovery for Open Textbook Library downloads.

The OTL API does not provide cover-image URLs. When the source file yields no
cover (see the generic helpers in ``gutenberg2zim.core.covers``), the cover is
fetched from the book's OTL page instead.
"""

from typing import Protocol
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from gutenberg2zim.constants import logger
from gutenberg2zim.core.rewriters.image_rewriter import ImageProcessor


class CoverFetchEngine(Protocol):
    """Minimal download interface required to fetch a page cover."""

    def fetch_bytes(self, url: str) -> bytes: ...


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
