"""Explicit ZIM writer wrapping `zimscraperlib.Creator`.

Replaces the `Global` static holder in `shared.py`: callers receive a
`ZimAssembler` instance instead of reaching for shared mutable state. All
write operations are serialized through an internal lock, so worker threads
may add items concurrently.
"""

import pathlib
import threading
from datetime import date

from zimscraperlib.zim.creator import Creator
from zimscraperlib.zim.indexing import IndexData
from zimscraperlib.zim.metadata import (
    CreatorMetadata,
    DateMetadata,
    DefaultIllustrationMetadata,
    DescriptionMetadata,
    LanguageMetadata,
    LongDescriptionMetadata,
    NameMetadata,
    PublisherMetadata,
    ScraperMetadata,
    StandardMetadataList,
    TagsMetadata,
    TitleMetadata,
)

from gutenberg2zim.constants import FAVICON_BYTES, VERSION, logger


class ZimAssembler:
    """Thread-safe wrapper around `zimscraperlib.Creator`."""

    def __init__(
        self,
        *,
        filename: pathlib.Path,
        language: str | list[str],
        title: str,
        description: str,
        name: str,
        publisher: str,
        source_creator: str,
        tags: str,
        long_description: str | None = None,
        scraper_name: str | None = None,
        with_fulltext_index: bool = True,
        debug: bool = False,
    ):
        self._lock = threading.Lock()
        self._creator = (
            Creator(
                filename=filename,
                main_path="index.html",
                workaround_nocancel=False,
            )
            .config_metadata(
                std_metadata=StandardMetadataList(
                    Title=TitleMetadata(title),
                    Description=DescriptionMetadata(description),
                    LongDescription=(
                        LongDescriptionMetadata(long_description)
                        if long_description and long_description.strip()
                        else None
                    ),
                    Creator=CreatorMetadata(source_creator),
                    Publisher=PublisherMetadata(publisher),
                    Name=NameMetadata(name),
                    Language=LanguageMetadata(language),
                    Tags=TagsMetadata(tags),
                    Scraper=ScraperMetadata(scraper_name or f"gutenberg2zim-{VERSION}"),
                    Date=DateMetadata(date.today()),
                    Illustration_48x48_at_1=DefaultIllustrationMetadata(FAVICON_BYTES),
                )
            )
            .config_verbose(debug)
            .config_indexing(with_fulltext_index)
        )

    @property
    def can_finish(self) -> bool:
        return self._creator.can_finish

    @can_finish.setter
    def can_finish(self, value: bool):
        self._creator.can_finish = value

    def start(self):
        self._creator.start()

    def add_item_for(
        self,
        path: str,
        title: str | None = None,
        fpath: pathlib.Path | None = None,
        content: str | bytes | None = None,
        mimetype: str | None = None,
        *,
        is_front: bool | None = None,
        should_compress: bool | None = None,
        delete_fpath: bool | None = False,
        auto_index: bool = False,
        index_data: IndexData | None = None,
    ):
        logger.debug(f"\t\tAdding ZIM item at {path}")

        if not mimetype and path.endswith(".epub"):
            mimetype = "application/epub+zip"

        with self._lock:
            self._creator.add_item_for(
                path=path,
                title=title,
                fpath=fpath,
                content=content,
                mimetype=mimetype,
                is_front=is_front,
                should_compress=should_compress,
                delete_fpath=delete_fpath,
                auto_index=auto_index,
                index_data=index_data,
            )

    def add_illustration(self, illus_fpath: pathlib.Path, illus_size: int):
        with open(illus_fpath, "rb") as fh:
            with self._lock:
                self._creator.add_illustration(illus_size, fh.read())

    def add_alias(self, path: str, title: str, target: str):
        """Add a ZIM alias from path to target (for images/data, not HTML)"""
        logger.debug(f"\t\tAdding ZIM alias from {path} to {target}")
        with self._lock:
            self._creator.add_alias(
                path=path,
                title=title,
                targetPath=target,
                hints={},
            )

    def finish(self):
        if self._creator.can_finish:
            logger.info("Finishing ZIM file")
            with self._lock:
                self._creator.finish()
            logger.info(
                f"Finished Zim {self._creator.filename.name} "
                f"in {self._creator.filename.parent}"
            )
