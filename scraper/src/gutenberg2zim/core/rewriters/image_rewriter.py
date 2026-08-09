"""Generic image rewriting and WebP conversion helpers.

Moved from the Gutenberg HTML rewriting module (originally `gutenberg2zim.export`).
Source-agnostic: nothing here knows about Gutenberg specifics.
"""

import io
from dataclasses import asdict
from pathlib import Path

from bs4 import BeautifulSoup
from PIL.Image import open as pilopen
from zimscraperlib.image.optimization import OptimizeWebpOptions

from gutenberg2zim.constants import logger

default_webp_options = asdict(OptimizeWebpOptions())


def rewrite_html_image_references(soup: BeautifulSoup, label: str) -> None:
    """Rewrite HTML image references to use .webp extension for converted images."""

    def rewrite_reference(element, attr, ref_type):
        """Helper to rewrite a single reference attribute."""
        if attr in element.attrs:
            old_ref = element[attr]
            new_ref = ImageProcessor.get_output_filename(old_ref)
            if old_ref != new_ref:
                element[attr] = new_ref
                logger.debug(f"{label}: Rewrote {ref_type} {old_ref} -> {new_ref}")

    # Rewrite <img> tags
    for img in soup.find_all("img"):
        rewrite_reference(img, "src", "image")

    # Rewrite <link rel="icon"> tags (for cover images in HTML head)
    for link in soup.find_all("link", rel="icon"):
        rewrite_reference(link, "href", "icon")


class ImageProcessor:
    """Centralized image processing logic for conversion decisions and operations."""

    @staticmethod
    def get_extension(filename: str) -> str:
        """Extract lowercase file extension without the dot."""
        return Path(filename).suffix[1:].lower()

    @staticmethod
    def should_convert_to_webp(filename: str) -> bool:
        """Check if file should be converted to WebP (JPG, JPEG, PNG only)."""
        return ImageProcessor.get_extension(filename) in ("jpg", "jpeg", "png")

    @staticmethod
    def get_output_filename(filename: str) -> str:
        """Get output filename with .webp extension if file will be converted."""
        if ImageProcessor.should_convert_to_webp(filename):
            return str(Path(filename).with_suffix(".webp"))
        return filename

    @staticmethod
    def optimize_image_content(file_content: bytes) -> bytes:
        """Convert and optimize image content to WebP format."""
        dst = io.BytesIO()
        with pilopen(io.BytesIO(file_content)) as image:
            image.save(dst, format="WEBP", **default_webp_options)
        return dst.getvalue()
