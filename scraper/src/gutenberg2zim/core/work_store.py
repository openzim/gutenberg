"""Explicit, thread-safe store for works.

Replaces the global `BookRepository` singleton: callers receive a `WorkStore`
instance instead of importing shared mutable state. Works are keyed by
(source, id) so works from different sources never collide.
"""

import threading

from gutenberg2zim.core.models import Work


class WorkStore:
    def __init__(self):
        self._works: dict[tuple[str, str], Work] = {}
        self._lock = threading.Lock()

    def add(self, work: Work):
        with self._lock:
            self._works[(work.source, work.id)] = work

    def get(self, source: str, work_id: str) -> Work | None:
        with self._lock:
            return self._works.get((source, work_id))

    def remove(self, source: str, work_id: str):
        with self._lock:
            self._works.pop((source, work_id), None)

    @property
    def works(self) -> list[Work]:
        with self._lock:
            return list(self._works.values())
