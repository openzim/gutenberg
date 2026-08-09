"""Tests for core.concurrency.parallel_map."""

import threading
import time

import pytest

from gutenberg2zim.core.concurrency import parallel_map


def test_processes_all_items():
    results = []
    lock = threading.Lock()

    def work(item):
        with lock:
            results.append(item)

    parallel_map(work, range(20), concurrency=4)
    assert sorted(results) == list(range(20))


def test_actually_parallelizes():
    # 8 items x 50ms of (GIL-releasing) sleep: serial would take >= 400ms,
    # with 4 workers it should finish in roughly 2 batches (~100ms)
    def work(_item):
        time.sleep(0.05)

    start = time.monotonic()
    parallel_map(work, range(8), concurrency=4)
    elapsed = time.monotonic() - start

    assert elapsed < 0.3  # generous margin against slow CI machines


def test_worker_exception_propagates():
    def work(item):
        if item == 3:
            raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        parallel_map(work, range(5), concurrency=2)


def test_single_worker_behaves_serially():
    results = []
    parallel_map(results.append, range(10), concurrency=1)
    assert results == list(range(10))
