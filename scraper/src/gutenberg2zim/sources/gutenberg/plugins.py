"""Gutenberg-specific HTML rewriting and book export (from `export.py`).

Contains everything needed to turn a Gutenberg HTML page into a static
offline page: charset normalization, image path transformation, internal
link rewriting, PG boilerplate ("*** START OF THE PROJECT GUTENBERG EBOOK")
removal, and infobox injection. Exposed through the source-agnostic
`RewriterPort` via `GutenbergHtmlRewriter`. Also holds the per-book ZIM
export (`export_book`) and EPUB optimization helpers.
"""

import io
import urllib.parse
import warnings
import zipfile
from pathlib import Path

import bs4
from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning
from jinja2 import Environment, PackageLoader, select_autoescape
from zimscraperlib.image.optimization import optimize_jpeg, optimize_png

from gutenberg2zim.constants import logger
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.ports import RewriterPort
from gutenberg2zim.core.rewriters.image_rewriter import (
    ImageProcessor,
    rewrite_html_image_references,
)
from gutenberg2zim.core.rewriters.link_rewriter import replacement_link
from gutenberg2zim.core.utils import (
    UTF8,
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    fname_for,
)
from gutenberg2zim.core.zim_assembler import ZimAssembler
from gutenberg2zim.sources.gutenberg.adapters import work_to_book
from gutenberg2zim.sources.gutenberg.downloader import download_book_cover
from gutenberg2zim.sources.gutenberg.models import Book

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class HtmlRewriteError(RuntimeError):
    """Raised when static HTML rewriting encounters an unexpected structure"""


infobox_jinja_env = Environment(
    loader=PackageLoader("gutenberg2zim", "templates"),
    autoescape=select_autoescape(("html", "htm", "xml")),
)
infobox_jinja_env.filters["book_name_for_fs"] = book_name_for_fs
infobox_jinja_env.filters["urlencode"] = urllib.parse.quote


def transform_image_path(book_id: int, path: str) -> str:
    """Transform image path from images/xxx to {book_id}_xxx"""
    return path.replace("images/", f"{book_id}_")


def update_html_for_static(
    book, html_content, formats, *, epub: bool = False, is_xml: bool = False
):
    soup = BeautifulSoup(html_content, "lxml-xml" if is_xml else "lxml")

    # Extract cover image href from <link rel="icon"> for later detection
    # and update its path to match image transformations
    if not epub:
        icon_link = soup.find("link", rel="icon")
        if icon_link:
            href = icon_link.get("href")
            if href and isinstance(href, str):
                # Store original href for cover detection (only once)
                if not book._cover_href:
                    book._cover_href = href

                # Transform the path
                icon_link["href"] = transform_image_path(book.book_id, href)

    # remove encoding as we're saving to UTF8 anyway
    encoding_specified = False
    for meta in soup.find_all("meta"):
        if "charset" in meta.attrs:
            encoding_specified = True
            # logger.debug("found <meta> tag with charset `{}`"
            #              .format(meta.attrs.get('charset')))
            del meta.attrs["charset"]
        elif "content" in meta.attrs and "charset=" in meta.get_attribute_list(
            "content"
        ):
            try:
                ctype, _ = meta.get_attribute_list("content")[0].split(";", 1)
            except Exception:  # noqa: S112
                continue
            else:
                encoding_specified = True
            # logger.debug("found <meta> tag with content;charset `{}`"
            #              .format(meta.attrs.get('content')))
            meta.attrs["content"] = ctype
    if encoding_specified:
        # logger.debug("charset was found and removed")
        pass

    # update all <img> links from images/xxx.xxx to {id}_xxx.xxx
    if not epub:
        for img in soup.find_all("img"):
            if "src" in img.attrs:
                img.attrs["src"] = transform_image_path(
                    book.book_id, img.get_attribute_list("src")[0]
                )

        # Rewrite image references to use .webp extension for converted images
        # This also handles <link rel="icon"> tags
        # Only for regular HTML, not EPUB (EPUB images are not converted to WebP)
        rewrite_html_image_references(soup, f"Book {book.book_id}")

    # update all <a> links to internal HTML pages
    # should only apply to relative URLs to HTML files.
    # examples on #16816, #22889, #30021
    if not epub:
        for link in soup.find_all("a"):
            new_link = replacement_link(
                item_id=book.book_id, url=str(link.attrs.get("href", ""))
            )
            if new_link is not None:
                link.attrs["href"] = new_link

    # Add the title
    if not epub:
        if soup.title:
            soup.title.string = book.title
        else:
            if not soup.html:
                raise HtmlRewriteError("HTML should be set")
            head = soup.find("head")
            if not head:
                head = soup.new_tag("head")
                soup.html.insert(0, head)
            title_tag = soup.new_tag("title")
            title_tag.string = book.title
            head.append(title_tag)

    patterns = [
        (
            "*** START OF THE PROJECT GUTENBERG EBOOK",
            "*** END OF THE PROJECT GUTENBERG EBOOK",
        ),
        (
            "***START OF THE PROJECT GUTENBERG EBOOK",
            "***END OF THE PROJECT GUTENBERG EBOOK",
        ),
        (
            "<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>",
            "<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>",
        ),
        # ePub only
        ("*** START OF THIS PROJECT GUTENBERG EBOOK", "*** START: FULL LICENSE ***"),
        (
            "*END THE SMALL PRINT! FOR PUBLIC DOMAIN ETEXT",
            "——————————————————————————-",
        ),
        (
            "*** START OF THIS PROJECT GUTENBERG EBOOK",
            "*** END OF THIS PROJECT GUTENBERG EBOOK",
        ),
        ("***START OF THE PROJECT GUTENBERG", "***END OF THE PROJECT GUTENBERG EBOOK"),
        (
            "COPYRIGHT PROTECTED ETEXTS*END*",
            "===========================================================",
        ),
        (
            "Nous remercions la Bibliothèque Nationale de France qui a mis à",
            "The Project Gutenberg Etext of",
        ),
        (
            "Nous remercions la Bibliothèque Nationale de France qui a mis à",
            "End of The Project Gutenberg EBook",
        ),
        (
            "=========================================================================",
            "——————————————————————————-",
        ),
        ("Project Gutenberg Etext", "End of Project Gutenberg Etext"),
        ("Text encoding is iso-8859-1", "Fin de Project Gutenberg Etext"),
        ("—————————————————-", "Encode an ISO 8859/1 Etext into LaTeX or HTML"),
    ]

    body = soup.find("body")
    if not isinstance(body, Tag):
        # No <body> to rewrite; return the original HTML unchanged
        return soup
    try:
        number_of_children_tags = sum(
            [1 for e in body.children if isinstance(e, bs4.Tag)]
        )
        number_of_children_div_tags = sum(
            [1 for e in body.children if isinstance(e, bs4.Tag) and e.name == "div"]
        )
        has_single_div = (
            number_of_children_tags == number_of_children_div_tags
            and number_of_children_tags == 1
        )
    except Exception:
        has_single_div = False

    if not has_single_div:
        for start_of_text, end_of_text in patterns:
            if start_of_text not in body.text and end_of_text not in body.text:
                continue

            if start_of_text in body.text and end_of_text in body.text:
                remove = True
                for child in body.children:
                    if not isinstance(child, bs4.Tag):
                        continue
                    if end_of_text in getattr(child, "text", ""):
                        remove = True
                    if start_of_text in getattr(child, "text", ""):
                        child.decompose()
                        remove = False
                    if remove:
                        child.decompose()
                break

            elif start_of_text in body.text:
                remove = True
                for child in body.children:
                    if not isinstance(child, bs4.Tag):
                        continue
                    if start_of_text in getattr(child, "text", ""):
                        child.decompose()
                        remove = False
                    if remove:
                        child.decompose()
                break
            elif end_of_text in body.text:
                remove = False
                for child in body.children:
                    if not isinstance(child, bs4.Tag):
                        continue
                    if end_of_text in getattr(child, "text", ""):
                        remove = True
                    if remove:
                        child.decompose()
                break

    # build infobox
    if not epub:
        infobox = infobox_jinja_env.get_template("book_infobox.html")
        infobox_html = infobox.render({"book": book, "formats": formats})
        info_soup = BeautifulSoup(infobox_html, "lxml")
        info_box = info_soup.find("div")
        if not isinstance(info_box, Tag):
            raise HtmlRewriteError("info_box div should be a Tag class")
        body.insert(0, info_box)

        # Ensure head exists
        head = soup.find("head")
        if not head:
            html = soup.find("html")
            if not isinstance(html, Tag):
                raise HtmlRewriteError("html should be a Tag class")
            head = soup.new_tag("head")
            html.insert(0, head)

        # Add CSS link if not already present in head
        if not head.find("link", {"href": "css/gutenberg-infobox.css"}):
            css_link = soup.new_tag(
                "link",
                rel="stylesheet",
                href="css/gutenberg-infobox.css",
                type="text/css",
            )
            head.append(css_link)

        # Add JS script at the end of body if not already present
        if not body.find("script", {"src": "js/gutenberg-infobox.js"}):
            js_script = soup.new_tag(
                "script", src="js/gutenberg-infobox.js", type="text/javascript"
            )
            body.append(js_script)

    # if there is no charset, set it to utf8
    if not epub:
        meta = BeautifulSoup(
            '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />',
            "lxml",
        )
        head = soup.find("head")
        html = soup.find("html")
        if not isinstance(head, Tag):
            raise HtmlRewriteError("head should be a Tag class")
        if not isinstance(html, Tag):
            raise HtmlRewriteError("html should be a Tag class")
        if not isinstance(meta.head, Tag):
            raise HtmlRewriteError("meta.head should be a Tag class")
        if head:
            head.insert(0, meta.head.contents[0])
        elif html:
            html.insert(0, meta.head)
        else:
            soup.insert(0, meta.head)

        return html

    return soup


def export_infobox_assets(assembler: ZimAssembler) -> None:
    """Export infobox CSS, JS, and icon files to ZIM"""
    templates_dir = Path(__file__).parent.parent.parent / "templates"

    assets = [
        ("css/gutenberg-infobox.css", "css", "text/css"),
        ("js/gutenberg-infobox.js", "js", "text/javascript"),
        ("icons/info.svg", "icons", "image/svg+xml"),
        ("icons/epub.svg", "icons", "image/svg+xml"),
        ("icons/pdf.svg", "icons", "image/svg+xml"),
        ("icons/scroll-up.svg", "icons", "image/svg+xml"),
    ]

    for zim_path, subdir, mimetype in assets:
        file_path = templates_dir / subdir / Path(zim_path).name
        if not file_path.exists():
            logger.warning(f"Infobox asset not found: {file_path}")
            continue
        logger.debug(f"Adding {zim_path} to ZIM")
        assembler.add_item_for(
            path=zim_path,
            fpath=file_path,
            mimetype=mimetype,
            is_front=False,
        )


class GutenbergHtmlRewriter(RewriterPort):
    """`RewriterPort` implementation for Gutenberg HTML pages.

    Note: the port goes through a Work -> legacy Book conversion, so the
    cover-href side effect (`book._cover_href`) of `update_html_for_static`
    is lost. Callers that rely on cover detection should keep using
    `update_html_for_static` directly until the pipeline is fully ported.
    """

    def __init__(self, formats: list[str]):
        self._formats = formats

    def rewrite_html(self, work: Work, html: BeautifulSoup) -> BeautifulSoup:
        result = update_html_for_static(
            book=work_to_book(work),
            html_content=str(html),
            formats=self._formats,
        )
        return BeautifulSoup(str(result), "lxml")


def export_book(
    book: Book,
    book_files: dict[str, bytes],
    formats: list[str],
    mirror_url: str,
    assembler: ZimAssembler,
    _zim_name: str,
    *,
    _title_search: bool,
    _add_lcc_shelves: bool,
):
    """Export book to ZIM using in-memory content"""
    handle_book_files(
        book=book,
        book_files=book_files,
        formats=formats,
        assembler=assembler,
    )

    # Handle cover image
    cover_path = f"covers/{book.book_id}_cover_image.webp"

    if book.html_cover_path:
        # HTML has a cover image - create alias instead of storing duplicate
        # Use alias (not redirect) since this is an image, not HTML with relative paths
        logger.debug(
            f"Using HTML cover for book #{book.book_id}: {book.html_cover_path}"
        )
        assembler.add_alias(
            path=cover_path,
            title="",
            target=book.html_cover_path,
        )
    else:
        # No HTML cover - download from mirror
        cover_image = download_book_cover(mirror_url, book)

        if cover_image:
            logger.debug(f"Using downloaded cover for book #{book.book_id}")
            # the mirror serves JPEG; convert to WebP to match cover_path/mimetype
            cover_image = ImageProcessor.optimize_image_content(cover_image)
            assembler.add_item_for(
                path=cover_path,
                content=cover_image,
                mimetype="image/webp",
                is_front=False,
            )


def handle_book_files(
    book: Book,
    book_files: dict[str, bytes],
    formats: list[str],
    assembler: ZimAssembler,
):
    """Handle book files from in-memory content and add to ZIM"""

    # Find the main HTML file
    main_html_filename = f"{book.book_id}.html"
    html_content = None

    if main_html_filename in book_files:
        html_content = book_files[main_html_filename].decode("utf-8", errors="replace")

    if html_content:
        article_name = article_name_for(book)
        new_html = update_html_for_static(
            book=book, html_content=html_content, formats=formats
        )

        # Add the optimized HTML directly to ZIM
        assembler.add_item_for(
            path=article_name,
            content=str(new_html),
            mimetype="text/html",
            is_front=False,
            title=book.title,
            auto_index=True,
        )

    # Handle other formats (epub, pdf)
    other_filenames = []
    for other_format in [
        fmt for fmt in book.requested_formats(formats) if fmt != "html"
    ]:
        book_filename = fname_for(book, other_format)
        if book_filename in book_files:
            other_filenames.append(book_filename)
            try:
                archive_name = archive_name_for(book, other_format)
                content = book_files[book_filename]
                if other_format == "epub":
                    content = optimize_epub_bytes(content, book)
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
                    book=book, html_content=html_str, formats=formats
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
                optimized_file_content = optimize_content(book, filename, file_content)
                output_filename = ImageProcessor.get_output_filename(filename)

                # Check if this is the cover image by comparing with transformed href
                # Note: filename is already transformed (e.g., "1_cover.jpg")
                # by download.py so we transform book._cover_href the same way
                if book._cover_href:
                    # Transform cover href same way we transform image paths
                    expected_cover = transform_image_path(
                        book.book_id, book._cover_href
                    )
                    expected_cover = ImageProcessor.get_output_filename(expected_cover)

                    if output_filename == expected_cover:
                        book.html_cover_path = output_filename
                        logger.debug(
                            f"Detected HTML cover for book #{book.book_id}: "
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


def optimize_content(book: Book, filename: str, file_content: bytes) -> bytes:
    """Optimize file content, converting images to WebP when appropriate."""
    # Convert JPG, PNG to WEBP for optimal file size
    if ImageProcessor.should_convert_to_webp(filename):
        return ImageProcessor.optimize_image_content(file_content)

    # Keep WebP and GIF files as-is
    ext = ImageProcessor.get_extension(filename)
    if ext in ("webp", "gif"):
        if ext == "gif":
            logger.debug(
                f"GIF file {filename} found in book {book.book_id} not optimized"
            )
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


def _process_epub_html(data: bytes, book: Book, *, is_xml: bool = False) -> bytes:
    """Process HTML file from EPUB: remove Gutenberg markers and process content."""
    html_str = data.decode("utf-8", errors="replace")
    soup = update_html_for_static(
        book=book, html_content=html_str, formats=[], epub=True, is_xml=is_xml
    )
    return str(soup).encode(UTF8)


def _process_epub_ncx(data: bytes, book: Book | None = None) -> bytes:
    """Process NCX navigation file: remove license section."""
    ncx_str = data.decode("utf-8", errors="replace")
    soup = BeautifulSoup(ncx_str, "lxml-xml")
    pattern = "*** START: FULL LICENSE ***"
    for tag in soup.find_all("text"):
        if pattern in tag.text:
            book_info = f"book {book.book_id}" if book else "unknown book"
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


def optimize_epub_bytes(epub_bytes: bytes, book: Book) -> bytes:
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
            data = src_zf.read(name)
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
                    f"Unexpected {suffix} image in EPUB for book {book.book_id}: {name}"
                )
            elif suffix in (".htm", ".html", ".xhtml"):
                data = _process_epub_html(data, book, is_xml=(suffix == ".xhtml"))
            elif suffix == ".ncx":
                data = _process_epub_ncx(data, book)

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
            f"Optimized EPUB for book {book.book_id} is larger than original: "
            f"{optimized_size} > {original_size} bytes"
        )
    else:
        logger.debug(
            f"Optimized EPUB for book {book.book_id}: "
            f"{optimized_size} < {original_size} bytes"
        )

    return optimized_bytes
