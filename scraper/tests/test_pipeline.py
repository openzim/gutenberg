"""Wiring smoke tests for core.pipeline.Pipeline with mocked ports (no network)"""

from unittest.mock import MagicMock, patch

import requests

from gutenberg2zim.core.models import Work
from gutenberg2zim.core.pipeline import (
    Pipeline,
    compute_flame_ratings,
)
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.core.progress import ScraperProgress
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.sources.gutenberg.catalog import GUTENBERG_SOURCE


def make_work(work_id: str, popularity: float | int) -> Work:
    return Work(
        id=work_id,
        source=GUTENBERG_SOURCE,
        title=f"Book {work_id}",
        popularity=popularity,
    )


class DummyPipeline(Pipeline):
    """Pipeline subclass recording hook calls instead of doing real work"""

    def __init__(self, calls: list[str], **kwargs):
        super().__init__(**kwargs)
        self.calls = calls

    def setup(self) -> None:
        self.calls.append("setup")

    def process_ref(self, ref: WorkRef) -> None:
        works = list(self.metadata.fetch([ref]))
        if works:
            self.store.add(works[0])
        self.calls.append(f"process:{ref.id}")

    def enrich_authors(self) -> None:
        self.calls.append("enrich")


def build_pipeline(calls: list[str], store: WorkStore) -> DummyPipeline:
    metadata = MagicMock(name="metadata")
    metadata.fetch.side_effect = lambda refs: [
        make_work(ref.id, popularity=100) for ref in refs
    ]
    return DummyPipeline(
        calls,
        metadata=metadata,
        store=store,
        assembler=MagicMock(name="assembler"),
        progress=ScraperProgress(None),
        concurrency=2,
        formats=["html"],
        zim_name="test",
        source_slug="test",
        display_name="Test Source",
    )


def test_run_calls_hooks_in_order_and_stores_works():
    calls: list[str] = []
    store = WorkStore()
    pipeline = build_pipeline(calls, store)
    refs = [WorkRef(id=str(i), source=GUTENBERG_SOURCE) for i in (1, 2, 3)]

    with (
        patch("gutenberg2zim.core.pipeline.generate_json_files") as mock_json,
        patch("gutenberg2zim.core.pipeline.generate_noscript_pages") as mock_nojs,
    ):
        mock_json.side_effect = lambda **_kwargs: calls.append("export")
        pipeline.run(refs)

    # setup hook ran first, then every ref was processed
    assert calls[0] == "setup"
    assert sorted(calls[1:]) == [
        "enrich",
        "export",
        "process:1",
        "process:2",
        "process:3",
    ]

    process_idxs = [
        index for index, call in enumerate(calls) if call.startswith("process")
    ]
    assert calls.index("enrich") > max(process_idxs)
    assert calls.index("export") > calls.index("enrich")

    # works were stored and flames were computed from their popularity
    assert len(store.works) == 3
    assert all(work.flames is not None for work in store.works)

    # final exports ran with the pipeline's store and assembler
    mock_json.assert_called_once()
    assert mock_json.call_args.kwargs["work_store"] is store
    assert mock_json.call_args.kwargs["assembler"] is pipeline.assembler
    mock_nojs.assert_called_once()
    assert mock_nojs.call_args.kwargs["work_store"] is store


def test_compute_flame_ratings_assigns_flames_from_source_scores():
    store = WorkStore()
    for work_id, downloads in [("1", 500), ("2", 300), ("3", 100), ("4", 0)]:
        store.add(make_work(work_id, popularity=downloads))

    compute_flame_ratings(store)

    flames = {work.id: work.flames or 0 for work in store.works}
    assert all(work.flames is not None for work in store.works)
    assert flames["1"] >= flames["2"]
    assert flames["2"] > flames["3"]
    assert flames["3"] > flames["4"]


def test_compute_flame_ratings_leaves_works_without_scores_unset():
    store = WorkStore()
    store.add(Work(id="1", source="opentextbooks", title="Textbook"))

    compute_flame_ratings(store)

    assert store.works[0].flames is None


def test_compute_flame_ratings_uses_work_popularity_scores():
    store = WorkStore()
    reviewed = [
        Work(
            id="1",
            source="opentextbooks",
            title="Excellent",
            popularity=4.9,
        ),
        Work(id="2", source="opentextbooks", title="Good", popularity=4.0),
        Work(id="3", source="opentextbooks", title="Fair", popularity=3.0),
    ]
    unreviewed = Work(id="4", source="opentextbooks", title="Unreviewed")
    for work in [*reviewed, unreviewed]:
        store.add(work)

    compute_flame_ratings(store)

    assert reviewed[0].flames is not None
    assert reviewed[1].flames is not None
    assert reviewed[2].flames is not None
    assert reviewed[0].flames >= reviewed[1].flames
    assert reviewed[1].flames > reviewed[2].flames
    assert unreviewed.flames is None


def test_no_book_level_retry_for_network_errors():
    """Network downloads retry individually inside the download helpers, so a
    RequestException escaping process_ref must NOT reprocess the whole book"""
    calls: list[str] = []
    store = WorkStore()
    pipeline = build_pipeline(calls, store)
    refs = [WorkRef(id=str(i), source=GUTENBERG_SOURCE) for i in (1, 2)]

    def flaky_process(ref: WorkRef):
        calls.append(f"process:{ref.id}")
        if ref.id == "1":
            raise requests.ConnectionError("network down")
        store.add(make_work(ref.id, popularity=100))

    pipeline.process_ref = flaky_process
    with (
        patch("gutenberg2zim.core.pipeline.generate_json_files"),
        patch("gutenberg2zim.core.pipeline.generate_noscript_pages"),
    ):
        pipeline.run(refs)

    # book 1 failed once (no whole-book reprocessing), book 2 still processed
    assert calls.count("process:1") == 1
    assert calls.count("process:2") == 1
