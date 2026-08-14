"""Per-work processing for Open Textbook Library."""

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import requests

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import DownloadEngine, is_fatal_http_error
from gutenberg2zim.core.models import Cover, Work
from gutenberg2zim.core.pipeline import Pipeline
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.core.utils import archive_name_for
from gutenberg2zim.sources.gutenberg.rewriter import export_html_reader_control_assets
from gutenberg2zim.sources.opentextbooks.covers import extract_cover, fetch_page_cover
from gutenberg2zim.sources.opentextbooks.html_mirror import (
    HtmlEdition,
    download_html_edition,
    is_html_document,
    set_download_controls,
)
from gutenberg2zim.sources.opentextbooks.invalid_urls import InvalidEditionCache
from gutenberg2zim.sources.opentextbooks.resolver import (
    OpenTextbookLibraryFormatResolver,
)


class OpenTextbookLibraryPipeline(Pipeline):
    """Download OTL editions, retaining HTML fallbacks for reader access."""

    def __init__(
        self, *, engine: DownloadEngine, cache_dir: Path | None = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.engine = engine
        self.resolver = OpenTextbookLibraryFormatResolver()
        self.invalid_urls = InvalidEditionCache(cache_dir)
        self._cover_executor = ThreadPoolExecutor(
            max_workers=min(4, self.concurrency), thread_name_prefix="otl-cover"
        )

    def run(self, refs: list[WorkRef]) -> None:
        try:
            export_html_reader_control_assets(self.assembler)
            super().run(refs)
        finally:
            self._cover_executor.shutdown(wait=True)

    def flame_score(self, work: Work) -> float | None:
        """Rank OTL works by the source's aggregate peer-review score."""
        score = work.extra.get("review_score")
        return float(score) if score is not None else None

    def process_ref(self, ref: WorkRef) -> None:
        works = list(self.metadata.fetch([ref]))
        if not works:
            return
        work = works[0]
        unsupported = work.extra.setdefault("unsupported_formats", [])
        downloaded = False
        html_downloaded = False
        downloaded_binary_formats: list[str] = []
        html_edition: HtmlEdition | None = None
        cover_image = None
        cover_future: Future[bytes | None] | None = None

        for format_name in sorted(
            self.formats, key=lambda format_name: format_name == "html"
        ):
            if format_name == "html" and html_downloaded:
                continue
            # Online editions can contain hundreds of separate pages. They
            # are the fallback when an OTL record has no usable binary edition,
            # rather than a duplicate of a valid PDF or EPUB.
            if format_name == "html" and downloaded:
                unsupported.append(format_name)
                continue
            request = self.resolver.resolve(work, format_name)
            if request is None:
                unsupported.append(format_name)
                continue
            if self.invalid_urls.contains(request.url):
                logger.debug("Skipping cached-invalid OTL edition URL: %s", request.url)
                unsupported.append(format_name)
                continue
            if format_name == "html":
                html_edition = download_html_edition(
                    self.engine, work, request.url, ["html"]
                )
                if html_edition is None:
                    logger.warning(
                        "OTL textbook #%s has no complete offline HTML edition: %s",
                        work.id,
                        request.url,
                    )
                    self.invalid_urls.add(request.url)
                    unsupported.append(format_name)
                    continue
                downloaded = True
                html_downloaded = True
                if cover_future is None:
                    cover_future = self._cover_executor.submit(
                        fetch_page_cover, self.engine, work.source_url
                    )
                continue
            try:
                content = self.engine.fetch_bytes(request.url)
            except requests.RequestException as exc:
                log = logger.debug if is_fatal_http_error(exc) else logger.warning
                log(
                    f"Could not download {format_name} for OTL textbook "
                    f"#{work.id}: {exc}"
                )
                if is_fatal_http_error(exc):
                    self.invalid_urls.add(request.url)
                unsupported.append(format_name)
                continue

            if is_html_document(content):
                logger.warning(
                    "OTL textbook #%s returned HTML instead of %s: %s",
                    work.id,
                    format_name.upper(),
                    request.url,
                )
                self.invalid_urls.add(request.url)
                unsupported.append(format_name)
                continue

            if not _is_valid_book_file(content, format_name):
                logger.warning(
                    f"OTL textbook #{work.id} returned a non-{format_name.upper()} "
                    f"response for {request.url}"
                )
                unsupported.append(format_name)
                continue

            media_type = next(
                (fmt.media_type for fmt in work.formats if fmt.url == request.url),
                "application/octet-stream",
            )
            self.assembler.add_item_for(
                path=archive_name_for(work, format_name),
                content=content,
                mimetype=media_type,
                is_front=False,
            )
            downloaded = True
            downloaded_binary_formats.append(format_name)
            if cover_image is None:
                cover_image = extract_cover(content, format_name)
            if cover_future is None:
                cover_future = self._cover_executor.submit(
                    fetch_page_cover, self.engine, work.source_url
                )

        if html_edition is not None:
            set_download_controls(html_edition, work, downloaded_binary_formats)
            for path, content in html_edition.pages.items():
                self.assembler.add_item_for(
                    path=path,
                    content=content,
                    mimetype="text/html",
                    is_front=False,
                )

        if downloaded:
            if cover_future is not None:
                page_cover = cover_future.result()
                if page_cover is not None:
                    cover_image = page_cover
            if cover_image:
                self.assembler.add_item_for(
                    path=f"covers/{work.id}_cover_image.webp",
                    content=cover_image,
                    mimetype="image/webp",
                    is_front=False,
                )
                work.cover = Cover()
                work.extra["has_cover"] = True
            self.store.add(work)
        else:
            logger.warning(
                f"OTL textbook #{work.id} has no downloadable requested format"
            )


def _is_valid_book_file(content: bytes, format_name: str) -> bool:
    """Reject landing pages masquerading as directly linked book files."""
    if format_name == "pdf":
        return content.lstrip().startswith(b"%PDF-")
    if format_name == "epub":
        return content.startswith(b"PK\x03\x04")
    if format_name == "html":
        return is_html_document(content)
    return False
