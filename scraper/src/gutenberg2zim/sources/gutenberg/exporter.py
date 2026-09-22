"""Per-book ZIM export orchestration for Gutenberg works."""

import re
from functools import partial

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.epub_optimizer import optimize_epub_bytes
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.rewriters.image_rewriter import ImageProcessor
from gutenberg2zim.core.utils import (
    archive_name_for,
    article_name_for,
    fname_for,
    requested_formats,
)
from gutenberg2zim.core.zim_assembler import ZimAssembler
from gutenberg2zim.sources.gutenberg.downloader import download_book_cover
from gutenberg2zim.sources.gutenberg.epub_optimize import (
    optimize_content,
    transform_epub_document,
)
from gutenberg2zim.sources.gutenberg.rewriter import (
    transform_image_path,
    update_html_for_static,
)

_COVER_BASENAME_RE = re.compile(r"^(?:cover|\d+-cover)\.(?:jpe?g|png|webp)$", re.I)


def is_cover_asset(work_id: str, filename: str) -> bool:
    """Return True when a book file is a Project Gutenberg cover asset"""
    prefix = f"{work_id}_"
    basename = filename[len(prefix) :] if filename.startswith(prefix) else filename
    return bool(_COVER_BASENAME_RE.match(basename))


def export_book(
    work: Work,
    book_files: dict[str, bytes],
    formats: list[str],
    mirror_url: str,
    assembler: ZimAssembler,
    engine: DownloadEngine,
    _zim_name: str,
    *,
    _title_search: bool,
):
    """Export book to ZIM using in-memory content"""
    handle_book_files(
        work=work,
        book_files=book_files,
        formats=formats,
        assembler=assembler,
    )

    # Handle cover image
    cover_path = f"covers/{work.id}_cover_image.webp"

    html_cover_path = work.extra.get("html_cover_path")
    if html_cover_path:
        # HTML has a cover image - create alias instead of storing duplicate
        # Use alias (not redirect) since this is an image, not HTML with relative paths
        logger.debug(f"Using HTML cover for book #{work.id}: {html_cover_path}")
        assembler.add_alias(
            path=cover_path,
            title="",
            target=html_cover_path,
        )
    else:
        # No HTML cover - download from mirror
        cover_image = download_book_cover(mirror_url, work, engine)

        if cover_image:
            logger.debug(f"Using downloaded cover for book #{work.id}")
            # the mirror serves JPEG; convert to WebP to match cover_path/mimetype
            cover_image = ImageProcessor.optimize_image_content(cover_image)
            assembler.add_item_for(
                path=cover_path,
                content=cover_image,
                mimetype="image/webp",
                is_front=False,
            )


def _add_main_html(
    work: Work,
    book_files: dict[str, bytes],
    formats: list[str],
    assembler: ZimAssembler,
    main_html_filename: str,
):
    if main_html_filename not in book_files:
        return
    html_content = book_files[main_html_filename].decode("utf-8", errors="replace")
    new_html = update_html_for_static(
        work=work, html_content=html_content, formats=formats
    )
    assembler.add_item_for(
        path=article_name_for(work),
        content=str(new_html),
        mimetype="text/html",
        is_front=False,
        title=work.title,
        auto_index=True,
    )


def _add_other_formats(
    work: Work,
    book_files: dict[str, bytes],
    formats: list[str],
    assembler: ZimAssembler,
):
    for other_format in [
        fmt for fmt in requested_formats(work, formats) if fmt != "html"
    ]:
        book_filename = fname_for(work, other_format)
        if book_filename not in book_files:
            continue
        try:
            content = book_files[book_filename]
            if other_format == "epub":
                content = optimize_epub_bytes(
                    content,
                    document_transform=partial(transform_epub_document, work=work),
                    log_context=f"book {work.id}",
                )
            assembler.add_item_for(
                path=archive_name_for(work, other_format),
                content=content,
                is_front=False,
            )
        except Exception as e:
            logger.exception(e)
            logger.error(f"\t\tException while handling {other_format}: {e}")
            raise


def _add_companion_html(
    work: Work,
    filename: str,
    file_content: bytes,
    formats: list[str],
    assembler: ZimAssembler,
):
    try:
        html_str = file_content.decode("utf-8", errors="replace")
        new_html = update_html_for_static(
            work=work, html_content=html_str, formats=formats
        )
        assembler.add_item_for(
            path=filename,
            content=str(new_html),
            mimetype="text/html",
            is_front=False,
        )
    except Exception as e:
        logger.exception(e)
        logger.error(f"\t\tException while handling companion HTML: {e}")


def _detect_html_cover(work: Work, filename: str, output_filename: str):
    if work.extra.get("html_cover_path"):
        return
    cover_href = work.extra.get("_cover_href")
    expected_cover = (
        ImageProcessor.get_output_filename(transform_image_path(work.id, cover_href))
        if cover_href
        else None
    )
    is_bundled_cover = (
        expected_cover is None
        and work.extra.get("has_cover")
        and is_cover_asset(work.id, filename)
    )
    if output_filename != expected_cover and not is_bundled_cover:
        return
    work.extra["html_cover_path"] = output_filename
    logger.debug(f"Detected HTML cover for book #{work.id}: {output_filename}")


def _add_asset_file(work: Work, filename: str, file_content: bytes, assembler):
    try:
        output_filename = ImageProcessor.get_output_filename(filename)
        optimized_file_content = optimize_content(work, filename, file_content)
        assembler.add_item_for(
            path=output_filename,
            content=optimized_file_content,
            is_front=False,
        )
        _detect_html_cover(work, filename, output_filename)
    except Exception as e:
        logger.exception(e)
        logger.error(f"\t\tException while handling file {filename}: {e}")


def _add_associated_files(
    work: Work,
    book_files: dict[str, bytes],
    formats: list[str],
    assembler: ZimAssembler,
    main_html_filename: str,
):
    other_filenames = {
        fname_for(work, fmt)
        for fmt in requested_formats(work, formats)
        if fmt != "html"
    }
    for filename, file_content in book_files.items():
        if filename == main_html_filename or filename in other_filenames:
            continue
        if filename.endswith((".html", ".htm")):
            _add_companion_html(work, filename, file_content, formats, assembler)
        else:
            _add_asset_file(work, filename, file_content, assembler)


def handle_book_files(
    work: Work,
    book_files: dict[str, bytes],
    formats: list[str],
    assembler: ZimAssembler,
):
    """Handle book files from in-memory content and add to ZIM"""
    main_html_filename = f"{work.id}.html"
    _add_main_html(work, book_files, formats, assembler, main_html_filename)
    _add_other_formats(work, book_files, formats, assembler)
    _add_associated_files(work, book_files, formats, assembler, main_html_filename)
