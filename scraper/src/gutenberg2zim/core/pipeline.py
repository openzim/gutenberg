"""Source-agnostic orchestration pipeline.

`Pipeline` drives the whole scrape once works have been discovered:

1. `setup()` hook (source-specific pre-processing, e.g. exporting static
   assets before any book is processed),
2. per-work processing in parallel with retry/backoff, via the
   source-specific `process_ref()` hook,
3. flame-rating computation using source-supplied scores,
4. final exports: JSON files and No-JS fallback pages (core exporters).

Sources supply their behavior by subclassing `Pipeline` (see
source pipeline implementations); there is deliberately no `ExportPort`
ABC — per-book download/rewrite/export is source-flavored and a
one-implementation interface would only fill the pattern.

Notes:
- Discovery (`CatalogPort.discover`) is NOT done here: the caller hands
  `run()` an already-discovered list of `WorkRef`s. The entrypoint owns
  filtering, empty-result handling, and progress totals, so discovery stays
  there.
- `DownloadEngine` lives outside this class: the caller (orchestrator) owns
  one engine and hands it to the metadata port and source pipeline; per-work
  transfers retry individually
  (see `core.download_engine.fetch_bytes_with_retry`).
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

import apsw
import backoff

from gutenberg2zim.constants import logger
from gutenberg2zim.core.concurrency import parallel_map
from gutenberg2zim.core.exporters.json_exporter import generate_json_files
from gutenberg2zim.core.exporters.nojs_exporter import generate_noscript_pages
from gutenberg2zim.core.exporters.search_items_exporter import export_search_items
from gutenberg2zim.core.index_builder import IndexBuilder
from gutenberg2zim.core.models import Work
from gutenberg2zim.core.ports import MetadataPort, WorkRef
from gutenberg2zim.core.progress import ScraperProgress
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler

NB_POPULARITY_FLAMES = 3


def compute_flame_ratings(
    store: WorkStore, score_for: Callable[[Work], float | int | None]
) -> None:
    """Bucket source-supplied scores into zero to three flames."""
    logger.info("Computing book flame ratings")
    all_works = store.works

    # Check if any works were successfully processed.
    if not all_works:
        logger.error("No books were successfully processed")
        raise RuntimeError(
            "All books failed to process. Cannot create ZIM without any content."
        )

    works_with_scores = sorted(
        ((work, score) for work in all_works if (score := score_for(work)) is not None),
        key=lambda item: item[1],
        reverse=True,
    )
    if not works_with_scores:
        logger.info("No flame-rating scores available; skipping computation")
        return

    all_works_count = len(works_with_scores)
    flame_limits = [0.0] * NB_POPULARITY_FLAMES
    flames = NB_POPULARITY_FLAMES
    score_value = works_with_scores[0][1]
    for iwork, (_, work_score) in enumerate(works_with_scores):
        if (
            iwork
            > float(NB_POPULARITY_FLAMES - flames + 1)
            / NB_POPULARITY_FLAMES
            * all_works_count
            and work_score < score_value
        ):
            flame_limits[flames - 1] = score_value
            flames = flames - 1
        score_value = work_score

    for work, work_score in works_with_scores:
        work.popularity = sum(
            [int(work_score >= flame_limits[i]) for i in range(NB_POPULARITY_FLAMES)]
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
        primary_color: str | None = None,
        secondary_color: str | None = None,
        # human-readable source name, used in ZIM titles, search entries
        # and No-JS page titles; the orchestrator passes
        # `SourceProfile.display_name`
        display_name: str,
        source_slug: str,
        source_description: str | None = None,
        collection_label: str = "Collections",
        collection_icon_style: str = "classification",
        title_search: bool = False,
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
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.display_name = display_name
        self.source_slug = source_slug
        self.source_description = source_description
        self.collection_label = collection_label
        self.collection_icon_style = collection_icon_style
        self.title_search = title_search

    def setup(self) -> None:
        """Hook run once before any work is processed (default: no-op)"""

    @abstractmethod
    def process_ref(self, ref: WorkRef) -> None:
        """Fetch metadata, download and export one work (source-specific)"""
        ...

    def compute_popularity(self) -> None:
        """Compute flame ratings after all works are processed."""
        compute_flame_ratings(self.store, self.flame_score)

    def flame_score(self, _work: Work) -> float | int | None:
        """Return this source's score for a work, or None when it has no score."""
        return None

    def run(self, refs: list[WorkRef]) -> None:
        """Orchestrate processing of discovered works and final exports"""
        self.setup()

        logger.info(
            f"Processing {len(refs)} books with {self.concurrency} (parallel) worker(s)"
        )

        def backoff_busy_error_hdlr(details):
            logger.warning(
                "Backing off {wait:0.1f} seconds after {tries} tries "
                "calling function {target} with args {args} and kwargs "
                "{kwargs} due to apsw.BusyError".format(**details)
            )

        # Only ZIM-write contention (apsw.BusyError) is retried at the book
        # level: network transfers retry individually (see
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

        self.compute_popularity()

        # Derived indexes (authors, per-author stats, search entries) built
        # once and shared by all exporters
        indexes = IndexBuilder(self.store).build(display_name=self.display_name)

        # Write the ZIM search index entries (books, authors, collections,
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
            primary_color=self.primary_color,
            secondary_color=self.secondary_color,
            display_name=self.display_name,
            source_slug=self.source_slug,
            source_description=self.source_description,
            collection_label=self.collection_label,
            collection_icon_style=self.collection_icon_style,
            indexes=indexes,
        )

        # Generate No-JS fallback pages
        logger.info("Generating No-JS fallback pages")
        generate_noscript_pages(
            formats=self.formats,
            work_store=self.store,
            assembler=self.assembler,
            display_name=self.display_name,
            collection_label=self.collection_label,
            indexes=indexes,
        )
