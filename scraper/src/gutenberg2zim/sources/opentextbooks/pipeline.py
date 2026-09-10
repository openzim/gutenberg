"""Per-work processing for Open Textbook Library."""

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import requests

from gutenberg2zim.constants import logger
from gutenberg2zim.core.content_validation import is_html_document, is_valid_book_file
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
    set_download_controls,
)
from gutenberg2zim.sources.opentextbooks.invalid_urls import InvalidEditionCache
from gutenberg2zim.sources.opentextbooks.resolver import (
    OpenTextbookLibraryFormatResolver,
)


@dataclass(slots=True)
class _DownloadedFormats:
    """Download state for one OTL work."""

    downloaded: bool = False
    html_downloaded: bool = False
    binary_formats: list[str] = field(default_factory=list)
    html_edition: HtmlEdition | None = None
    cover_image: bytes | None = None
    cover_future: Future[bytes | None] | None = None


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
        downloaded_formats = self._download_requested_formats(work, unsupported)

        if downloaded_formats.html_edition is not None:
            set_download_controls(
                downloaded_formats.html_edition, work, downloaded_formats.binary_formats
            )
            for path, content in downloaded_formats.html_edition.pages.items():
                self.assembler.add_item_for(
                    path=path,
                    content=content,
                    mimetype="text/html",
                    is_front=False,
                )

        if downloaded_formats.downloaded:
            if downloaded_formats.cover_future is not None:
                page_cover = downloaded_formats.cover_future.result()
                if page_cover is not None:
                    downloaded_formats.cover_image = page_cover
            if downloaded_formats.cover_image:
                self.assembler.add_item_for(
                    path=f"covers/{work.id}_cover_image.webp",
                    content=downloaded_formats.cover_image,
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

    def _download_requested_formats(
        self, work: Work, unsupported: list[str]
    ) -> _DownloadedFormats:
        """Download binary editions, using online HTML only as a fallback."""
        result = _DownloadedFormats()
        for format_name in sorted(
            self.formats, key=lambda format_name: format_name == "html"
        ):
            self._download_format(work, format_name, unsupported, result)
        return result

    def _download_format(
        self,
        work: Work,
        format_name: str,
        unsupported: list[str],
        result: _DownloadedFormats,
    ) -> None:
        if format_name == "html" and (result.html_downloaded or result.downloaded):
            if not result.html_downloaded:
                unsupported.append(format_name)
            return

        request = self.resolver.resolve(work, format_name)
        if request is None:
            unsupported.append(format_name)
            return
        if self.invalid_urls.contains(request.url):
            logger.debug("Skipping cached-invalid OTL edition URL: %s", request.url)
            unsupported.append(format_name)
            return

        if format_name == "html":
            self._download_html_format(work, request.url, unsupported, result)
        else:
            self._download_binary_format(
                work, format_name, request.url, unsupported, result
            )

    def _download_html_format(
        self,
        work: Work,
        url: str,
        unsupported: list[str],
        result: _DownloadedFormats,
    ) -> None:
        edition = download_html_edition(self.engine, work, url, ["html"])
        if edition is None:
            logger.warning(
                "OTL textbook #%s has no complete offline HTML edition: %s",
                work.id,
                url,
            )
            self.invalid_urls.add(url)
            unsupported.append("html")
            return
        result.html_edition = edition
        result.html_downloaded = True
        result.downloaded = True
        result.cover_future = self._schedule_page_cover(work, result.cover_future)

    def _download_binary_format(
        self,
        work: Work,
        format_name: str,
        url: str,
        unsupported: list[str],
        result: _DownloadedFormats,
    ) -> None:
        try:
            content = self.engine.fetch_bytes(url)
        except requests.RequestException as exc:
            log = logger.debug if is_fatal_http_error(exc) else logger.warning
            log(f"Could not download {format_name} for OTL textbook #{work.id}: {exc}")
            if is_fatal_http_error(exc):
                self.invalid_urls.add(url)
            unsupported.append(format_name)
            return

        if is_html_document(content):
            logger.warning(
                "OTL textbook #%s returned HTML instead of %s: %s",
                work.id,
                format_name.upper(),
                url,
            )
            self.invalid_urls.add(url)
            unsupported.append(format_name)
            return
        if not is_valid_book_file(content, format_name):
            logger.warning(
                "OTL textbook #%s returned a non-%s response for %s",
                work.id,
                format_name.upper(),
                url,
            )
            unsupported.append(format_name)
            return

        self.assembler.add_item_for(
            path=archive_name_for(work, format_name),
            content=content,
            mimetype=next(
                (fmt.media_type for fmt in work.formats if fmt.url == url),
                "application/octet-stream",
            ),
            is_front=False,
        )
        result.downloaded = True
        result.binary_formats.append(format_name)
        if result.cover_image is None:
            result.cover_image = extract_cover(content, format_name)
        result.cover_future = self._schedule_page_cover(work, result.cover_future)

    def _schedule_page_cover(
        self, work: Work, future: Future[bytes | None] | None
    ) -> Future[bytes | None]:
        """Fetch the source cover once, in parallel with remaining downloads."""
        return future or self._cover_executor.submit(
            fetch_page_cover, self.engine, work.source_url
        )
