"""Source-agnostic concurrency helper.

Just a thin wrapper around a thread pool so the pipeline (and later other
callers) does not repeat the `Pool(...).map(...)` incantation.
"""

from collections.abc import Callable, Iterable
from multiprocessing.dummy import Pool


def parallel_map[T](func: Callable[[T], None], items: Iterable[T], concurrency: int):
    """Map func over items using a thread pool with `concurrency` workers"""
    with Pool(concurrency) as pool:
        pool.map(func, items)
