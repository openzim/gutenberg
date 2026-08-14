"""Offline mirroring of OTL's explicitly declared online editions."""

import hashlib
import posixpath
import re
from collections import deque
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import is_fatal_http_error
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.rewriters.image_rewriter import ImageProcessor
from gutenberg2zim.core.utils import archive_name_for, article_name_for

MAX_HTML_PAGES = 300
MAX_HTML_ASSETS = 500
MAX_HTML_EDITION_BYTES = 64 * 1024 * 1024
MIN_HTML_TEXT_LENGTH = 600
CSS_URL_PATTERN = re.compile(r"url\((?P<quote>['\"]?)(?P<url>[^)'\"]+)(?P=quote)\)")


@dataclass(frozen=True, slots=True)
class HtmlEdition:
    """A root page and its offline companion pages, keyed by ZIM path."""

    pages: dict[str, bytes]


class FetchEngine(Protocol):
    """Minimal download interface required for mirroring an HTML edition."""

    def fetch_bytes(self, url: str) -> bytes: ...


def download_html_edition(
    engine: FetchEngine, work: Work, url: str, formats: list[str]
) -> HtmlEdition | None:
    """Mirror a self-contained online edition or its same-site chapter pages.

    A response to a PDF/EPUB URL is never considered an HTML edition.  This
    function only processes the source's explicitly declared ``Online`` URL.
    It follows HTML pages, stylesheets and images within that edition's URL
    directory and rewrites their references to offline ZIM counterparts.
    """
    root_url = _canonical_url(url)
    root = urlparse(root_url)
    root_directory = root.path.rsplit("/", 1)[0] + "/"
    root_path = article_name_for(work)
    urls = deque([root_url])
    content_by_url: dict[str, bytes] = {}
    path_by_url = {root_url: root_path}
    asset_urls: deque[str] = deque()
    asset_content_by_url: dict[str, bytes] = {}
    downloaded_bytes = 0
    byte_budget_reached = False

    def fetch_with_budget(resource_url: str) -> bytes | None:
        nonlocal downloaded_bytes, byte_budget_reached
        content = engine.fetch_bytes(resource_url)
        if len(content) > MAX_HTML_EDITION_BYTES - downloaded_bytes:
            byte_budget_reached = True
            logger.warning(
                "Stopping OTL online-edition mirror for textbook #%s after %s MiB",
                work.id,
                MAX_HTML_EDITION_BYTES // (1024 * 1024),
            )
            return None
        downloaded_bytes += len(content)
        if downloaded_bytes == MAX_HTML_EDITION_BYTES:
            byte_budget_reached = True
        return content

    while urls and len(content_by_url) < MAX_HTML_PAGES and not byte_budget_reached:
        page_url = urls.popleft()
        try:
            content = fetch_with_budget(page_url)
        except requests.RequestException as exc:
            log = logger.debug if is_fatal_http_error(exc) else logger.warning
            log(
                "Could not download online edition page for OTL textbook #%s: %s",
                work.id,
                exc,
            )
            continue
        if content is None:
            break
        if not is_html_document(content):
            continue

        content_by_url[page_url] = content
        soup = BeautifulSoup(content, "html.parser")
        for link in soup.select("a[href]"):
            href = link.get("href")
            if not isinstance(href, str):
                continue
            linked_url = _internal_html_url(page_url, href, root, root_directory)
            if linked_url is None or linked_url in path_by_url:
                continue
            path_by_url[linked_url] = _companion_path(work, linked_url)
            urls.append(linked_url)
        _discover_html_assets(
            soup, page_url, root, root_directory, path_by_url, asset_urls, work
        )

    root_content = content_by_url.get(root_url)
    if root_content is None or not _is_complete_edition(root_content, content_by_url):
        return None

    while (
        asset_urls
        and len(asset_content_by_url) < MAX_HTML_ASSETS
        and not byte_budget_reached
    ):
        asset_url = asset_urls.popleft()
        try:
            content = fetch_with_budget(asset_url)
        except requests.RequestException as exc:
            logger.debug(
                "Could not download OTL online-edition asset %s: %s", asset_url, exc
            )
            continue
        if content is None:
            break
        asset_content_by_url[asset_url] = content
        if _is_css_url(asset_url):
            _discover_css_assets(
                content, asset_url, root, root_directory, path_by_url, asset_urls, work
            )

    output_assets: dict[str, bytes] = {}
    for asset_url, asset_content in asset_content_by_url.items():
        asset_path = path_by_url[asset_url]
        output_content = asset_content
        if _is_css_url(asset_url):
            pass
        elif ImageProcessor.should_convert_to_webp(asset_path):
            try:
                output_content = ImageProcessor.optimize_image_content(asset_content)
                asset_path = ImageProcessor.get_output_filename(asset_path)
                path_by_url[asset_url] = asset_path
            except Exception as exc:
                logger.debug(
                    "Could not convert OTL asset %s to WebP: %s", asset_url, exc
                )
        output_assets[asset_url] = output_content

    pages: dict[str, bytes] = {}
    for page_url, content in content_by_url.items():
        page_path = path_by_url[page_url]
        soup = BeautifulSoup(content, "html.parser")
        _rewrite_html_references(soup, page_url, page_path, path_by_url)
        _inject_reader_controls(soup, page_path, work, formats)
        pages[page_path] = str(soup).encode("utf-8")
    for asset_url, output_content in output_assets.items():
        asset_path = path_by_url[asset_url]
        final_content = output_content
        if _is_css_url(asset_url):
            final_content = _rewrite_css_references(
                output_content, asset_url, asset_path, path_by_url
            )
        pages[asset_path] = final_content
    return HtmlEdition(pages=pages)


def set_download_controls(
    edition: HtmlEdition, work: Work, available_formats: list[str]
) -> None:
    """Update mirrored HTML controls with formats actually stored in the ZIM."""
    for page_path, content in edition.pages.items():
        if not is_html_document(content):
            continue
        soup = BeautifulSoup(content, "html.parser")
        if controls := soup.find(id="html-reader-controls"):
            controls.decompose()
        _inject_reader_controls(soup, page_path, work, available_formats)
        edition.pages[page_path] = str(soup).encode("utf-8")


def _is_complete_edition(root_content: bytes, pages: dict[str, bytes]) -> bool:
    """Reject generic landing pages while allowing a book page or a real TOC."""
    soup = BeautifulSoup(root_content, "html.parser")
    for element in soup(["script", "style", "noscript", "nav", "header", "footer"]):
        element.decompose()
    text_length = len(soup.get_text(" ", strip=True))
    # A long page can itself be a complete book chapter. A shorter table of
    # contents is accepted only when at least one linked chapter was mirrored.
    return text_length >= MIN_HTML_TEXT_LENGTH and len(pages) > 1


def _internal_html_url(
    page_url: str, href: str, root, root_directory: str
) -> str | None:
    target_url, _ = urldefrag(urljoin(page_url, href))
    if not target_url:
        return None
    target = urlparse(target_url)
    if (
        target.scheme not in {"http", "https"}
        or target.netloc != root.netloc
        or not target.path.startswith(root_directory)
        or not _is_html_path(target.path)
    ):
        return None
    return _canonical_url(target_url)


def _discover_html_assets(
    soup: BeautifulSoup,
    page_url: str,
    root,
    root_directory: str,
    path_by_url: dict[str, str],
    asset_urls: deque[str],
    work: Work,
) -> None:
    for element, attribute in (
        *[(link, "href") for link in soup.select("link[href]")],
        *[(image, "src") for image in soup.select("img[src], source[src]")],
    ):
        reference = element.get(attribute)
        if not isinstance(reference, str):
            continue
        asset_url = _internal_asset_url(page_url, reference, root, root_directory)
        if asset_url is not None:
            _queue_asset(asset_url, path_by_url, asset_urls, work)


def _discover_css_assets(
    content: bytes,
    stylesheet_url: str,
    root,
    root_directory: str,
    path_by_url: dict[str, str],
    asset_urls: deque[str],
    work: Work,
) -> None:
    css = content.decode("utf-8", errors="replace")
    for match in CSS_URL_PATTERN.finditer(css):
        asset_url = _internal_asset_url(
            stylesheet_url, match["url"], root, root_directory
        )
        if asset_url is not None:
            _queue_asset(asset_url, path_by_url, asset_urls, work)


def _queue_asset(
    url: str, path_by_url: dict[str, str], asset_urls: deque[str], work: Work
) -> None:
    if url in path_by_url:
        return
    path_by_url[url] = _asset_path(work, url)
    asset_urls.append(url)


def _internal_asset_url(
    page_url: str, reference: str, root, root_directory: str
) -> str | None:
    target_url, _ = urldefrag(urljoin(page_url, reference))
    target = urlparse(target_url)
    if (
        target.scheme not in {"http", "https"}
        or target.netloc != root.netloc
        or not target.path.startswith(root_directory)
    ):
        return None
    return _canonical_url(target_url)


def _rewrite_html_references(
    soup: BeautifulSoup, page_url: str, page_path: str, path_by_url: dict[str, str]
) -> None:
    for element, attribute in (
        *[(link, "href") for link in soup.select("a[href], link[href]")],
        *[(image, "src") for image in soup.select("img[src], source[src]")],
    ):
        _rewrite_reference(element, attribute, page_url, page_path, path_by_url)


def _inject_reader_controls(
    soup: BeautifulSoup, page_path: str, work: Work, formats: list[str]
) -> None:
    """Add shared reader controls and available binary downloads to an OTL page."""
    html = soup.html or soup.new_tag("html")
    if soup.html is None:
        soup.append(html)
    head = soup.head
    if head is None:
        head = soup.new_tag("head")
        html.insert(0, head)
    body = soup.body
    if body is None:
        body = soup.new_tag("body")
        html.append(body)

    assets_base = posixpath.relpath(".", posixpath.dirname(page_path)) or "."
    index_path = posixpath.relpath("index.html", posixpath.dirname(page_path))
    css_path = f"{assets_base}/css/html-reader-controls.css"
    js_path = f"{assets_base}/js/html-reader-controls.js"
    if not head.find("link", href=css_path):
        stylesheet = soup.new_tag("link", rel="stylesheet", href=css_path)
        stylesheet["type"] = "text/css"
        head.append(stylesheet)

    if not body.find(id="html-reader-controls"):
        controls = soup.new_tag("div", id="html-reader-controls")
        info = soup.new_tag(
            "a",
            attrs={
                "href": f"{index_path}#/book/{work.id}",
                "class": "html-reader-btn html-reader-btn-info",
                "aria-label": "View book cover and information",
                "title": "View book cover and information",
            },
        )
        info.append(
            soup.new_tag(
                "img",
                src=f"{assets_base}/icons/info.svg",
                alt="Info",
                width="24",
                height="24",
            )
        )
        controls.append(info)
        for format_name in formats:
            if format_name not in {"epub", "pdf"}:
                continue
            archive_path = archive_name_for(work, format_name)
            download = soup.new_tag(
                "a",
                attrs={
                    "href": posixpath.relpath(
                        archive_path, posixpath.dirname(page_path)
                    ),
                    "class": f"html-reader-btn html-reader-btn-{format_name}",
                    "aria-label": f"Download {format_name.upper()} format",
                    "title": f"Download {format_name.upper()} format",
                },
            )
            download.append(
                soup.new_tag(
                    "img",
                    src=f"{assets_base}/icons/{format_name}.svg",
                    alt=format_name.upper(),
                    width="24",
                    height="24",
                )
            )
            controls.append(download)
        scroll = soup.new_tag(
            "a",
            attrs={
                "href": "#",
                "id": "scroll-to-top",
                "class": "html-reader-btn html-reader-btn-up hidden",
                "aria-label": "Scroll to top",
                "title": "Scroll to top",
            },
        )
        scroll.append(
            soup.new_tag(
                "img",
                src=f"{assets_base}/icons/scroll-up.svg",
                alt="Scroll to top",
                width="24",
                height="24",
            )
        )
        controls.append(scroll)
        body.insert(0, controls)
    if not body.find("script", src=js_path):
        script = soup.new_tag("script", src=js_path)
        script["type"] = "text/javascript"
        body.append(script)


def _rewrite_css_references(
    content: bytes, css_url: str, css_path: str, path_by_url: dict[str, str]
) -> bytes:
    css = content.decode("utf-8", errors="replace")

    def replace(match: re.Match[str]) -> str:
        target_url, fragment = urldefrag(urljoin(css_url, match["url"]))
        target_path = path_by_url.get(_canonical_url(target_url))
        if target_path is None:
            return match.group(0)
        relative = posixpath.relpath(target_path, posixpath.dirname(css_path))
        if fragment:
            relative = f"{relative}#{fragment}"
        return f"url({match['quote']}{relative}{match['quote']})"

    return CSS_URL_PATTERN.sub(replace, css).encode("utf-8")


def _rewrite_reference(
    element, attribute: str, page_url: str, page_path: str, path_by_url: dict[str, str]
) -> None:
    target_url, fragment = urldefrag(urljoin(page_url, element[attribute]))
    target_path = path_by_url.get(_canonical_url(target_url))
    if target_path is None:
        return
    relative = posixpath.relpath(target_path, posixpath.dirname(page_path))
    element[attribute] = f"{relative}#{fragment}" if fragment else relative


def _is_html_path(path: str) -> bool:
    return path.endswith("/") or path.lower().endswith((".html", ".htm"))


def _canonical_url(url: str) -> str:
    return urldefrag(url)[0]


def _companion_path(work: Work, url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"html/{work.id}/{digest}.html"


def _asset_path(work: Work, url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    suffix = posixpath.splitext(urlparse(url).path)[1] or ".bin"
    return f"html/{work.id}/assets/{digest}{suffix}"


def _is_css_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".css")


def is_html_document(content: bytes) -> bool:
    prefix = content.lstrip()[:512].lower()
    return (
        prefix.startswith(b"<!doctype html")
        or prefix.startswith(b"<html")
        or b"<html" in prefix
    )
