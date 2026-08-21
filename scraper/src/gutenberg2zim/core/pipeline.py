"""Source-agnostic orchestration pipeline.

`Pipeline` drives the whole scrape once works have been discovered:

1. `setup()` hook (source-specific pre-processing, e.g. exporting static
   assets before any book is processed),
2. per-work processing in parallel with retry/backoff, via the
   source-specific `process_ref()` hook,
3. popularity computation (star bucketing over download counts),
4. final exports: JSON files and No-JS fallback pages (core exporters).

Sources supply their behavior by subclassing `Pipeline` (see
`sources/gutenberg/pipeline.py`); there is deliberately no `ExportPort`
ABC — per-book download/rewrite/export is source-flavored and a
one-implementation interface would only fill the pattern.

Notes:
- Discovery (`CatalogPort.discover`) is NOT done here: the caller hands
  `run()` an already-discovered list of `WorkRef`s. For Gutenberg the
  entrypoint needs the filtered catalog entries anyway (language metadata,
  empty-result error, progress total), so discovery stays there.
- Downloads go through `DownloadEngine`, which lives outside this class:
  the caller (orchestrator) owns one engine and hands it to the metadata
  port and the source pipeline; per-book downloads retry individually
  (see `core.download_engine.fetch_bytes_with_retry`).
"""

from abc import ABC, abstractmethod

import apsw
import backoff

from gutenberg2zim.constants import logger
from gutenberg2zim.core.concurrency import parallel_map
from gutenberg2zim.core.exporters.json_exporter import generate_json_files
from gutenberg2zim.core.exporters.nojs_exporter import generate_noscript_pages
from gutenberg2zim.core.exporters.search_items_exporter import export_search_items
from gutenberg2zim.core.index_builder import IndexBuilder
from gutenberg2zim.core.ports import MetadataPort, WorkRef
from gutenberg2zim.core.progress import ScraperProgress
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler

NB_POPULARITY_STARS = 3


def compute_popularity(store: WorkStore) -> None:
    """Compute popularity stars for all works based on download counts"""
    # Compute popularity (a bit too late for rendering on books pages,
    # but still useful for sorting)
    logger.info("Computing book popularity")
    all_works = sorted(
        store.works,
        key=lambda work: work.extra.get("downloads", 0),
        reverse=True,
    )

    # Check if any books were successfully downloaded
    if not all_works:
        logger.error("No books were successfully processed")
        raise RuntimeError(
            "All books failed to process. Cannot create ZIM without any content."
        )

    all_works_count = len(all_works)
    stars_limits = [0] * NB_POPULARITY_STARS
    stars = NB_POPULARITY_STARS
    nb_downloads = all_works[0].extra.get("downloads", 0)
    for iwork in range(0, len(all_works), 1):
        work_downloads = all_works[iwork].extra.get("downloads", 0)
        if (
            iwork
            > float(NB_POPULARITY_STARS - stars + 1)
            / NB_POPULARITY_STARS
            * all_works_count
            and work_downloads < nb_downloads
        ):
            stars_limits[stars - 1] = nb_downloads
            stars = stars - 1
        nb_downloads = work_downloads

    for work in all_works:
        work.popularity = sum(
            [
                int(work.extra.get("downloads", 0) >= stars_limits[i])
                for i in range(NB_POPULARITY_STARS)
            ]
        )
        # Write the computed popularity back into the store
        store.add(work)


class Pipeline(ABC):
    """Source-agnostic scrape orchestrator; sources subclass the hooks"""

    def __init__(
        self,
        *,
        metadata: MetadataPort,
        store: WorkStore,
        assembler: ZimAssembler,
        progress: ScraperProgress,
        concurrency: int,
        formats: list[str],
        zim_name: str,
        title: str | None = None,
        description: str | None = None,
        add_lcc_shelves: bool,
        primary_color: str | None = None,
        secondary_color: str | None = None,
        # human-readable source name, used in ZIM titles, search entries
        # and No-JS page titles; the orchestrator passes
        # `SourceProfile.display_name`
        display_name: str,
    ):
        self.metadata = metadata
        self.store = store
        self.assembler = assembler
        self.progress = progress
        self.concurrency = concurrency
        self.formats = formats
        self.zim_name = zim_name
        self.title = title
        self.description = description
        self.add_lcc_shelves = add_lcc_shelves
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.display_name = display_name

    def setup(self) -> None:
        """Hook run once before any work is processed (default: no-op)"""

    @abstractmethod
    def process_ref(self, ref: WorkRef) -> None:
        """Fetch metadata, download and export one work (source-specific)"""
        ...

    def run(self, refs: list[WorkRef]) -> None:
        """Orchestrate processing of discovered works and final exports"""
        self.setup()

        logger.info(
            f"Processing {len(refs)} books with "
            f"{self.concurrency} (parallel) worker(s)"
        )

        def backoff_busy_error_hdlr(details):
            logger.warning(
                "Backing off {wait:0.1f} seconds after {tries} tries "
                "calling function {target} with args {args} and kwargs "
                "{kwargs} due to apsw.BusyError".format(**details)
            )

        # Only ZIM-write contention (apsw.BusyError) is retried at the book
        # level: network downloads retry individually (see
        # core.download_engine.fetch_bytes_with_retry), so a RequestException
        # reaching this point already exhausted its own retries
        @backoff.on_exception(
            backoff.constant,
            apsw.BusyError,
            max_time=3,
            on_backoff=backoff_busy_error_hdlr,
        )
        def process_ref_with_retry(ref: WorkRef):
            """Process one work with retry logic"""
            self.process_ref(ref)

        def process_one(ref: WorkRef):
            try:
                process_ref_with_retry(ref)
            except Exception:
                logger.error(
                    f"Fatal error received with processing book {ref.id}",
                    exc_info=True,
                )
            self.progress.increase_progress()

        parallel_map(process_one, refs, self.concurrency)

        compute_popularity(self.store)

        # Derived indexes (authors, per-author stats, search entries) built
        # once and shared by all exporters
        indexes = IndexBuilder(self.store).build(
            add_lcc_shelves=self.add_lcc_shelves, display_name=self.display_name
        )

        # Write the ZIM search index entries (books, authors, shelves,
        # listing pages) pointing at the UI routes
        export_search_items(indexes, self.assembler)

        # export to JSON files (new format for Vue.js UI)
        logger.info("Generating JSON files for Vue.js UI")
        generate_json_files(
            zim_name=self.zim_name,
            formats=self.formats,
            work_store=self.store,
            assembler=self.assembler,
            title=self.title,
            description=self.description,
            add_lcc_shelves=self.add_lcc_shelves,
            primary_color=self.primary_color,
            secondary_color=self.secondary_color,
            display_name=self.display_name,
            indexes=indexes,
        )

        # Generate No-JS fallback pages
        logger.info("Generating No-JS fallback pages")
        generate_noscript_pages(
            formats=self.formats,
            work_store=self.store,
            assembler=self.assembler,
            display_name=self.display_name,
            indexes=indexes,
        )
