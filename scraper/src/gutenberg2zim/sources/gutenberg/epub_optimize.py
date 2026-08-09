"""In-memory EPUB/binary optimization helpers for Gutenberg book files."""

import io
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup
from zimscraperlib.image.optimization import optimize_jpeg, optimize_png

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


def _optimize_epub_jpeg(data: bytes) -> bytes:
    """Optimize JPEG image in-memory for EPUB, keeping original format."""
    dst = io.BytesIO()
    optimize_jpeg(src=io.BytesIO(data), dst=dst)
    return dst.getvalue()


def _optimize_epub_png(data: bytes) -> bytes:
    """Optimize PNG image in-memory for EPUB, keeping original format."""
    dst = io.BytesIO()
    optimize_png(src=io.BytesIO(data), dst=dst)
    return dst.getvalue()


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


def optimize_epub_bytes(epub_bytes: bytes, work: Work) -> bytes:
    """Optimize EPUB in-memory: process HTML/NCX and optimize images without FS."""
    src_buf = io.BytesIO(epub_bytes)
    dst_buf = io.BytesIO()
    original_size = len(epub_bytes)

    with (
        zipfile.ZipFile(src_buf, "r") as src_zf,
        zipfile.ZipFile(dst_buf, "w", zipfile.ZIP_DEFLATED) as dst_zf,
    ):
        infos = src_zf.infolist()
        mimetype_info = next(
            (info for info in infos if info.filename == "mimetype"), None
        )
        if mimetype_info is None:
            raise ValueError("EPUB is missing its mimetype entry")

        # Write mimetype first, uncompressed, per EPUB spec
        dst_zf.writestr(
            "mimetype",
            src_zf.read(mimetype_info),
            compress_type=zipfile.ZIP_STORED,
        )

        for info in infos:
            if info.filename == "mimetype":
                continue

            name = info.filename
            # read by ZipInfo, not name: with duplicate member names, read(name)
            # would return the last duplicate for every entry
            data = src_zf.read(info)
            suffix = Path(name).suffix.lower()

            if suffix in (".jpg", ".jpeg"):
                optimized_data = _optimize_epub_jpeg(data)
                if len(optimized_data) < len(data):  # ignore bigger compressed version
                    data = optimized_data
            elif suffix == ".png":
                optimized_data = _optimize_epub_png(data)
                if len(optimized_data) < len(data):  # ignore bigger compressed version
                    data = optimized_data
            elif suffix in (".gif", ".webp"):
                logger.warning(
                    f"Unexpected {suffix} image in EPUB for book {work.id}: {name}"
                )
            elif suffix in (".htm", ".html", ".xhtml"):
                data = _process_epub_html(data, work, is_xml=(suffix == ".xhtml"))
            elif suffix == ".ncx":
                data = _process_epub_ncx(data, work)

            # copy metadata but force deflate: the source ZipInfo's
            # compress_type would otherwise override the archive default
            out_info = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
            out_info.external_attr = info.external_attr
            out_info.compress_type = zipfile.ZIP_DEFLATED
            dst_zf.writestr(out_info, data)

    optimized_bytes = dst_buf.getvalue()
    optimized_size = len(optimized_bytes)
    if optimized_size > original_size:
        logger.warning(
            f"Optimized EPUB for book {work.id} is larger than original: "
            f"{optimized_size} > {original_size} bytes"
        )
    else:
        logger.debug(
            f"Optimized EPUB for book {work.id}: "
            f"{optimized_size} < {original_size} bytes"
        )

    return optimized_bytes
