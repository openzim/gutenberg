"""Explicit scrape configuration.

Replaces the ad-hoc passing of CLI arguments through the call stack: the
entrypoint builds one immutable `ScrapeConfig` and hands it to the pipeline,
which forwards it (or parts of it) to the components that need it.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ScrapeConfig:
    source: str
    mirror_url: str
    output_folder: Path
    zim_file: Path
    concurrency: int = 16
    formats: list[str] = field(default_factory=lambda: ["epub", "pdf", "html"])
    books: list[str] | None = None
    languages: list[str] | None = None
    collections: list[str] | None = None
    ui_dist: Path | None = None
    temp_dir: Path | None = None
    debug: bool = False
