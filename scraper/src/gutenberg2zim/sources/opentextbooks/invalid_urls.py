"""Persistent cache of external OTL edition URLs known to be unusable."""

import json
import threading
from pathlib import Path

from gutenberg2zim.core.utils import atomic_write_text


class InvalidEditionCache:
    """Remember invalid format URLs without caching downloaded book content."""

    def __init__(self, cache_dir: Path | None):
        self._path = cache_dir / "otl_invalid_edition_urls.json" if cache_dir else None
        self._lock = threading.Lock()
        self._urls: set[str] = set()
        try:
            data = (
                json.loads(self._path.read_text(encoding="utf-8")) if self._path else []
            )
            self._urls = set(data) if isinstance(data, list) else set()
        except OSError, json.JSONDecodeError:
            pass

    def contains(self, url: str) -> bool:
        with self._lock:
            return url in self._urls

    def add(self, url: str) -> None:
        with self._lock:
            if url in self._urls:
                return
            self._urls.add(url)
            if self._path:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write_text(
                    self._path,
                    json.dumps(sorted(self._urls), indent=2) + "\n",
                )
