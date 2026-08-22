"""Per-book ZIM export orchestration for Gutenberg works."""

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import DownloadEngine
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
    optimize_epub_bytes,
)
from gutenberg2zim.sources.gutenberg.rewriter import (
    transform_image_path,
    update_html_for_static,
)


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


def handle_book_files(
    work: Work,
    book_files: dict[str, bytes],
    formats: list[str],
    assembler: ZimAssembler,
):
    """Handle book files from in-memory content and add to ZIM"""

    # Find the main HTML file
    main_html_filename = f"{work.id}.html"
    html_content = None

    if main_html_filename in book_files:
        html_content = book_files[main_html_filename].decode("utf-8", errors="replace")

    if html_content:
        article_name = article_name_for(work)
        new_html = update_html_for_static(
            work=work, html_content=html_content, formats=formats
        )

        # Add the optimized HTML directly to ZIM
        assembler.add_item_for(
            path=article_name,
            content=str(new_html),
            mimetype="text/html",
            is_front=False,
            title=work.title,
            auto_index=True,
        )

    # Handle other formats (epub, pdf)
    other_filenames = []
    for other_format in [
        fmt for fmt in requested_formats(work, formats) if fmt != "html"
    ]:
        book_filename = fname_for(work, other_format)
        if book_filename in book_files:
            other_filenames.append(book_filename)
            try:
                archive_name = archive_name_for(work, other_format)
                content = book_files[book_filename]
                if other_format == "epub":
                    content = optimize_epub_bytes(content, work)
                assembler.add_item_for(
                    path=archive_name,
                    content=content,
                    is_front=False,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling {other_format}: {e}")
                raise

    # Process all associated files (images, companion HTML files, etc)
    for filename, file_content in book_files.items():
        # Skip the main HTML file as it's already processed
        if filename == main_html_filename:
            continue

        # Skip files matching a specific format since they have already been processed
        if filename in other_filenames:
            continue

        if filename.endswith((".html", ".htm")):
            # Process companion HTML files
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
        else:
            # Add other files (images, etc) directly
            try:
                optimized_file_content = optimize_content(work, filename, file_content)
                output_filename = ImageProcessor.get_output_filename(filename)

                # Check if this is the cover image by comparing with transformed href
                # Note: filename is already transformed (e.g., "1_cover.jpg")
                # by download.py so we transform the stored cover href the same way
                cover_href = work.extra.get("_cover_href")
                if cover_href:
                    # Transform cover href same way we transform image paths
                    expected_cover = transform_image_path(work.id, cover_href)
                    expected_cover = ImageProcessor.get_output_filename(expected_cover)

                    if output_filename == expected_cover:
                        work.extra["html_cover_path"] = output_filename
                        logger.debug(
                            f"Detected HTML cover for book #{work.id}: "
                            f"{output_filename}"
                        )

                assembler.add_item_for(
                    path=output_filename,
                    content=optimized_file_content,
                    is_front=False,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling file {filename}: {e}")
