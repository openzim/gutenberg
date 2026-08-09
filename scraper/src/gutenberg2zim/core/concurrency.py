"""Source-agnostic concurrency helper.

Just a thin wrapper around a thread pool so the pipeline (and later other
callers) does not repeat the `Pool(...)` incantation.
"""

from collections.abc import Callable, Iterable
from multiprocessing.dummy import Pool


def parallel_map[T](func: Callable[[T], None], items: Iterable[T], concurrency: int):
    """Map func over items using a thread pool with `concurrency` workers.

    Uses `imap_unordered` with chunksize 1: work is dispatched lazily (the
    whole item list is not chunked up front) and workers never wait on
    ordering. An exception not handled by ``func`` is raised in the caller
    when its failed result is consumed; this stops iteration and terminates
    the pool, although work already running may finish first. Callers may
    intentionally handle per-item failures before they reach this helper.
    """
    with Pool(concurrency) as pool:
        for _ in pool.imap_unordered(func, items, chunksize=1):
            pass
