"""Per-work processing for Wikisource.

Each work is downloaded from ws-export in the requested binary formats (epub in
practice), validated, and added to the ZIM together with a cover extracted from
the book file. Formats ws-export does not serve for a given work are recorded as
unsupported, mirroring the other sources' drop-format behavior.
"""

import requests

from gutenberg2zim.constants import logger
from gutenberg2zim.core.content_validation import is_html_document, is_valid_book_file
from gutenberg2zim.core.covers import extract_cover
from gutenberg2zim.core.download_engine import DownloadEngine, is_fatal_http_error
from gutenberg2zim.core.models import Cover, Work
from gutenberg2zim.core.pipeline import Pipeline
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.core.utils import archive_name_for
from gutenberg2zim.sources.wikisource.resolver import WikisourceFormatResolver


class WikisourcePipeline(Pipeline):
    """Download ws-export editions and add them to the ZIM."""

    def __init__(self, *, engine: DownloadEngine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self.resolver = WikisourceFormatResolver()

    def process_ref(self, ref: WorkRef) -> None:
        works = list(self.metadata.fetch([ref]))
        if not works:
            return
        work = works[0]
        unsupported = work.extra.setdefault("unsupported_formats", [])

        downloaded = False
        cover_image: bytes | None = None
        for format_name in self.formats:
            content = self._download_format(work, format_name, unsupported)
            if content is None:
                continue
            downloaded = True
            if cover_image is None:
                cover_image = extract_cover(content, format_name)

        if not downloaded:
            logger.warning(
                "Wikisource book %s has no downloadable requested format", work.id
            )
            return

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

    def _download_format(
        self, work: Work, format_name: str, unsupported: list[str]
    ) -> bytes | None:
        request = self.resolver.resolve(work, format_name)
        if request is None:
            unsupported.append(format_name)
            return None
        try:
            content = self.engine.fetch_bytes(request.url)
        except requests.RequestException as exc:
            log = logger.debug if is_fatal_http_error(exc) else logger.warning
            log("Could not download %s for %s: %s", format_name, work.id, exc)
            unsupported.append(format_name)
            return None

        if is_html_document(content) or not is_valid_book_file(content, format_name):
            logger.warning(
                "Wikisource book %s returned an invalid %s response: %s",
                work.id,
                format_name.upper(),
                request.url,
            )
            unsupported.append(format_name)
            return None

        self.assembler.add_item_for(
            path=archive_name_for(work, format_name),
            content=content,
            mimetype=next(
                (fmt.media_type for fmt in work.formats if fmt.name == format_name),
                "application/octet-stream",
            ),
            is_front=False,
        )
        return content
