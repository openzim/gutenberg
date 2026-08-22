"""Gutenberg-specific HTML rewriting.

Everything needed to turn a Gutenberg HTML page into a static offline page:
charset normalization, image path transformation, internal link rewriting,
PG boilerplate ("*** START OF THE PROJECT GUTENBERG EBOOK") removal, and
infobox injection. Exposed through the source-agnostic `RewriterPort` via
`GutenbergHtmlRewriter`.
"""

import urllib.parse
import warnings
from importlib import resources
from pathlib import Path

import bs4
from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning
from jinja2 import Environment, PackageLoader, select_autoescape

from gutenberg2zim.constants import logger
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.ports import RewriterPort
from gutenberg2zim.core.rewriters.image_rewriter import rewrite_html_image_references
from gutenberg2zim.core.rewriters.link_rewriter import replacement_link
from gutenberg2zim.core.utils import book_name_for_fs, work_template_context
from gutenberg2zim.core.zim_assembler import ZimAssembler

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class HtmlRewriteError(RuntimeError):
    """Raised when static HTML rewriting encounters an unexpected structure"""


infobox_jinja_env = Environment(
    loader=PackageLoader("gutenberg2zim", "templates"),
    autoescape=select_autoescape(("html", "htm", "xml")),
)
infobox_jinja_env.filters["book_name_for_fs"] = book_name_for_fs
infobox_jinja_env.filters["urlencode"] = urllib.parse.quote


def transform_image_path(book_id: str, path: str) -> str:
    """Transform image path from images/xxx to {book_id}_xxx"""
    return path.replace("images/", f"{book_id}_")


def update_html_for_static(
    work: Work,
    html_content: str,
    formats: list[str],
    *,
    epub: bool = False,
    is_xml: bool = False,
) -> BeautifulSoup:
    soup = BeautifulSoup(html_content, "lxml-xml" if is_xml else "lxml")

    # Extract cover image href from <link rel="icon"> for later detection
    # and update its path to match image transformations
    if not epub:
        icon_link = soup.find("link", rel="icon")
        if icon_link:
            href = icon_link.get("href")
            if href and isinstance(href, str):
                # Store original href for cover detection (only once)
                if not work.extra.get("_cover_href"):
                    work.extra["_cover_href"] = href

                # Transform the path
                icon_link["href"] = transform_image_path(work.id, href)

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
                    work.id, img.get_attribute_list("src")[0]
                )

        # Rewrite image references to use .webp extension for converted images
        # This also handles <link rel="icon"> tags
        # Only for regular HTML, not EPUB (EPUB images are not converted to WebP)
        rewrite_html_image_references(soup, f"Book {work.id}")

    # update all <a> links to internal HTML pages
    # should only apply to relative URLs to HTML files.
    # examples on #16816, #22889, #30021
    if not epub:
        for link in soup.find_all("a"):
            new_link = replacement_link(
                item_id=work.id, url=str(link.attrs.get("href", ""))
            )
            if new_link is not None:
                link.attrs["href"] = new_link

    # Add the title
    if not epub:
        if soup.title:
            soup.title.string = work.title
        else:
            if not soup.html:
                raise HtmlRewriteError("HTML should be set")
            head = soup.find("head")
            if not head:
                head = soup.new_tag("head")
                soup.html.insert(0, head)
            title_tag = soup.new_tag("title")
            title_tag.string = work.title
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
        infobox_html = infobox.render(
            {"book": work_template_context(work), "formats": formats}
        )
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
        if not head.find("link", {"href": "css/html-reader-controls.css"}):
            css_link = soup.new_tag(
                "link",
                rel="stylesheet",
                href="css/html-reader-controls.css",
                type="text/css",
            )
            head.append(css_link)

        # Add JS script at the end of body if not already present
        if not body.find("script", {"src": "js/html-reader-controls.js"}):
            js_script = soup.new_tag(
                "script", src="js/html-reader-controls.js", type="text/javascript"
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
        head.insert(0, meta.head.contents[0])

    return soup


def export_html_reader_control_assets(assembler: ZimAssembler) -> None:
    """Export shared HTML-reader controls and icons to the ZIM."""
    templates_dir = resources.files("gutenberg2zim") / "templates"

    assets = [
        ("css/html-reader-controls.css", "css", "text/css"),
        ("js/html-reader-controls.js", "js", "text/javascript"),
        ("icons/info.svg", "icons", "image/svg+xml"),
        ("icons/epub.svg", "icons", "image/svg+xml"),
        ("icons/pdf.svg", "icons", "image/svg+xml"),
        ("icons/scroll-up.svg", "icons", "image/svg+xml"),
    ]

    for zim_path, subdir, mimetype in assets:
        resource = templates_dir / subdir / Path(zim_path).name
        if not resource.is_file():
            raise HtmlRewriteError(f"Infobox asset not found: {resource}")
        logger.debug(f"Adding {zim_path} to ZIM")
        assembler.add_item_for(
            path=zim_path,
            content=resource.read_bytes(),
            mimetype=mimetype,
            is_front=False,
        )


class GutenbergHtmlRewriter(RewriterPort):
    """`RewriterPort` implementation for Gutenberg HTML pages"""

    def __init__(self, formats: list[str]):
        self._formats = formats

    def rewrite_html(self, work: Work, html: BeautifulSoup) -> BeautifulSoup:
        result = update_html_for_static(
            work=work,
            html_content=str(html),
            formats=self._formats,
        )
        return BeautifulSoup(str(result), "lxml")
