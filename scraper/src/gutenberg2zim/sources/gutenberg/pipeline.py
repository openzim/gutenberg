"""Gutenberg `Pipeline` implementation.

Supplies the source-specific hooks of `core.pipeline.Pipeline`:
- `setup()`: export the infobox CSS/JS/icon assets first, to fail fast,
- `process_ref()`: fetch metadata through the `MetadataPort`, download the
  book in-memory with `download_book` through the shared `DownloadEngine`
  and export it with `export_book`. HTML rewriting still calls
  `update_html_for_static` inside `export_book` (see `GutenbergHtmlRewriter`'s
  docstring for why the port is not used there yet).
"""

from gutenberg2zim.constants import logger
from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.pipeline import Pipeline
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.sources.gutenberg.downloader import download_book
from gutenberg2zim.sources.gutenberg.exporter import export_book
from gutenberg2zim.sources.gutenberg.rewriter import export_infobox_assets


class GutenbergPipeline(Pipeline):
    """Per-book pipeline for the Gutenberg source, wired through ports"""

    def __init__(
        self, *, mirror_url: str, engine: DownloadEngine, title_search: bool, **kwargs
    ):
        super().__init__(**kwargs)
        self.mirror_url = mirror_url
        self.engine = engine
        self.title_search = title_search

    def setup(self) -> None:
        # Export infobox assets (CSS, JS, and icons) first to fail fast if
        # there's an issue
        logger.info("Exporting infobox assets")
        export_infobox_assets(self.assembler)

    def process_ref(self, ref: WorkRef) -> None:
        """Fetch metadata, download book content and export directly to ZIM"""
        works = list(self.metadata.fetch([ref]))
        if not works:
            return
        work = works[0]
        self.store.add(work)

        book_content = download_book(
            mirror_url=self.mirror_url,
            work=work,
            formats=self.formats,
            work_store=self.store,
            engine=self.engine,
        )

        if book_content:
            export_book(
                work=work,
                book_files=book_content.files,
                formats=self.formats,
                mirror_url=self.mirror_url,
                assembler=self.assembler,
                engine=self.engine,
                _zim_name=self.zim_name,
                _title_search=self.title_search,
                _add_lcc_shelves=self.add_lcc_shelves,
            )
