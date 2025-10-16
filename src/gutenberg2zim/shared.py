import pathlib
import threading
from datetime import date
from typing import Any

from zimscraperlib.zim.creator import Creator
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


class Global:
    """Shared context accross all scraper components"""

    creator: Creator
    default_context: dict[str, Any] | None
    default_context_project_id: str | None

    _lock = threading.Lock()

    @staticmethod
    def setup(
        filename,
        language,
        title,
        description,
        long_description,
        name,
        publisher,
        with_fulltext_index,
    ):
        Global.default_context = None
        Global.default_context_project_id = None
        Global.creator = (
            Creator(
                filename=filename,
                main_path="Home",
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
                    Creator=CreatorMetadata("gutenberg.org"),
                    Publisher=PublisherMetadata(publisher),
                    Name=NameMetadata(name),
                    Language=LanguageMetadata(language),
                    Tags=TagsMetadata("_category:gutenberg;gutenberg"),
                    Scraper=ScraperMetadata(f"gutenberg2zim-{VERSION}"),
                    Date=DateMetadata(date.today()),
                    Illustration_48x48_at_1=DefaultIllustrationMetadata(FAVICON_BYTES),
                )
            )
            .config_verbose(True)
            .config_indexing(with_fulltext_index)
        )

    @staticmethod
    def add_item_for(
        path: str,
        title: str | None = None,
        fpath: pathlib.Path | None = None,
        content: str | bytes | None = None,
        mimetype: str | None = None,
        *,
        is_front: bool | None = None,
        should_compress: bool | None = None,
        delete_fpath: bool | None = False,
    ):
        logger.debug(f"\t\tAdding ZIM item at {path}")

        if not mimetype and path.endswith(".epub"):
            mimetype = "application/epub+zip"

        with Global._lock:

            Global.creator.add_item_for(
                path=path,
                title=title,
                fpath=fpath,
                content=content,
                mimetype=mimetype,
                is_front=is_front,
                should_compress=should_compress,
                delete_fpath=delete_fpath,
            )

    @staticmethod
    def add_illustration(illus_fpath, illus_size):
        with open(illus_fpath, "rb") as fh:
            with Global._lock:
                Global.creator.add_illustration(illus_size, fh.read())

    @staticmethod
    def start():
        Global.creator.start()

    @staticmethod
    def finish():
        if Global.creator.can_finish:
            logger.info("Finishing ZIM file")
            with Global._lock:
                Global.creator.finish()
            logger.info(
                f"Finished Zim {Global.creator.filename.name} "
                f"in {Global.creator.filename.parent}"
            )
