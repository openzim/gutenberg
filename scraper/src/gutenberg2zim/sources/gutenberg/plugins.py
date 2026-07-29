"""Gutenberg-specific HTML rewriting (moved from `gutenberg2zim.export`).

Contains everything needed to turn a Gutenberg HTML page into a static
offline page: charset normalization, image path transformation, internal
link rewriting, PG boilerplate ("*** START OF THE PROJECT GUTENBERG EBOOK")
removal, and infobox injection. Exposed through the source-agnostic
`RewriterPort` via `GutenbergHtmlRewriter`.
"""

import io
import urllib.parse
from dataclasses import asdict
from pathlib import Path

import bs4
from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, PackageLoader, select_autoescape
from PIL.Image import open as pilopen
from zimscraperlib.image.optimization import OptimizeWebpOptions

from gutenberg2zim.adapters import work_to_book
from gutenberg2zim.constants import logger
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.ports import RewriterPort
from gutenberg2zim.utils import book_name_for_fs

default_webp_options = asdict(OptimizeWebpOptions())


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
        rewrite_html_image_references(soup, book)

    # update all <a> links to internal HTML pages
    # should only apply to relative URLs to HTML files.
    # examples on #16816, #22889, #30021
    def replacablement_link(book, url):
        try:
            urlp, anchor = url.rsplit("#", 1)
        except ValueError:
            urlp = url
            anchor = None
        if "/" in urlp:
            return None

        if len(urlp.strip()):
            nurl = f"{book.book_id}_{urlp}"
        else:
            nurl = ""

        if anchor is not None:
            return "#".join([nurl, anchor])

        return nurl

    if not epub:
        for link in soup.find_all("a"):
            new_link = replacablement_link(book=book, url=link.attrs.get("href", ""))
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


def rewrite_html_image_references(soup: BeautifulSoup, book) -> None:
    """Rewrite HTML image references to use .webp extension for converted images."""

    def rewrite_reference(element, attr, ref_type):
        """Helper to rewrite a single reference attribute."""
        if attr in element.attrs:
            old_ref = element[attr]
            new_ref = ImageProcessor.get_output_filename(old_ref)
            if old_ref != new_ref:
                element[attr] = new_ref
                logger.debug(
                    f"Book {book.book_id}: Rewrote {ref_type} {old_ref} -> {new_ref}"
                )

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
