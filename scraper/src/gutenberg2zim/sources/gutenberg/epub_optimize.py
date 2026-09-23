"""Gutenberg-specific EPUB document and HTML asset transforms."""

from bs4 import BeautifulSoup

from gutenberg2zim.constants import logger
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.rewriters.image_rewriter import ImageProcessor
from gutenberg2zim.core.utils import UTF8
from gutenberg2zim.sources.gutenberg.rewriter import update_html_for_static


def optimize_content(work: Work, filename: str, file_content: bytes) -> bytes:
    """Optimize file content, converting images to WebP when appropriate."""
    # Convert JPG, PNG to WEBP for optimal file size
    if ImageProcessor.should_convert_to_webp(filename):
        return ImageProcessor.optimize_image_content(file_content)

    # Keep WebP and GIF files as-is
    ext = ImageProcessor.get_extension(filename)
    if ext in ("webp", "gif"):
        if ext == "gif":
            logger.debug(f"GIF file {filename} found in book {work.id} not optimized")
        return file_content

    # Do not optimize other file types
    return file_content


def _process_epub_html(data: bytes, work: Work, *, is_xml: bool = False) -> bytes:
    """Process HTML file from EPUB: remove Gutenberg markers and process content."""
    html_str = data.decode("utf-8", errors="replace")
    soup = update_html_for_static(
        work=work, html_content=html_str, formats=[], epub=True, is_xml=is_xml
    )
    return str(soup).encode(UTF8)


def _process_epub_ncx(data: bytes, work: Work | None = None) -> bytes:
    """Process NCX navigation file: remove license section."""
    ncx_str = data.decode("utf-8", errors="replace")
    soup = BeautifulSoup(ncx_str, "lxml-xml")
    pattern = "*** START: FULL LICENSE ***"
    for tag in soup.find_all("text"):
        if pattern in tag.text:
            book_info = f"book {work.id}" if work else "unknown book"
            logger.info(f"Found license section in NCX for {book_info}")
            s = tag.parent.parent if tag.parent else None
            if s is None:
                logger.warning(f"Unexpected NCX structure for {book_info}")
                break
            # Collect siblings before decomposing (decompose breaks iteration)
            siblings_to_remove = list(s.next_siblings)
            s.decompose()
            for sibling in siblings_to_remove:
                if hasattr(sibling, "decompose"):  # Skip text nodes
                    sibling.decompose()
            break
    return str(soup).encode(UTF8)


def transform_epub_document(filename: str, data: bytes, work: Work) -> bytes:
    """Apply Gutenberg-only cleanup to an EPUB document member."""
    lowercase_filename = filename.lower()
    if lowercase_filename.endswith((".htm", ".html", ".xhtml")):
        return _process_epub_html(
            data, work, is_xml=lowercase_filename.endswith(".xhtml")
        )
    if lowercase_filename.endswith(".ncx"):
        return _process_epub_ncx(data, work)
    return data
