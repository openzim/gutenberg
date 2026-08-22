"""Explicit scrape configuration.

Replaces the ad-hoc passing of CLI arguments through the call stack: the
entrypoint builds one immutable `ScrapeConfig` and hands it to the pipeline,
which forwards it (or parts of it) to the components that need it.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zimscraperlib.image.probing import is_hex_color
from zimscraperlib.inputs import compute_descriptions

from gutenberg2zim.core.utils import ALL_FORMATS, critical_error
from gutenberg2zim.sources.registry import get_source


@dataclass(frozen=True, slots=True)
class ScrapeConfig:
    source: str
    mirror_url: str
    output_folder: Path
    cache_dir: Path | None = None
    concurrency: int = 16
    formats: list[str] = field(default_factory=lambda: ["epub", "pdf", "html"])
    books: list[str] | None = None
    languages: list[str] | None = None
    collections: list[str] | None = None
    source_options: dict[str, Any] = field(default_factory=dict)
    ui_dist: Path | None = None
    temp_dir: Path | None = None
    debug: bool = False
    zim_file: str | None = None
    zim_name: str | None = None
    title: str | None = None
    description: str | None = None
    long_description: str | None = None
    zim_languages: list[str] | None = None
    publisher: str = "openZIM"
    overwrite: bool = False
    is_selection: bool = False
    title_search: bool = False
    with_fulltext_index: bool = True
    stats_filename: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None


def _validate_colors(primary_color: str | None, secondary_color: str | None) -> None:
    """Validate hex color formats if provided"""
    if primary_color and not is_hex_color(primary_color):
        critical_error(f"--primary-color is not a valid hex color: {primary_color}")
    if secondary_color and not is_hex_color(secondary_color):
        critical_error(f"--secondary-color is not a valid hex color: {secondary_color}")


def build_scrape_config(arguments: dict) -> ScrapeConfig:
    """Turn parsed CLI arguments (docopt result) into a `ScrapeConfig`"""
    zim_file = arguments.get("--zim-file")
    zim_name = arguments.get("--zim-name")
    source = get_source(arguments.get("--source") or "gutenberg")
    source_options = source.parse_cli_options(arguments)
    mirror_url = arguments.get("--mirror-url") or source.default_mirror_url

    books_csv = arguments.get("--books") or ""
    zim_title = arguments.get("--zim-title")

    zim_desc = arguments.get("--zim-desc")
    zim_long_description = arguments.get("--zim-long-desc")

    concurrency = int(arguments.get("--concurrency") or 16)
    if concurrency <= 0:
        critical_error(f"--concurrency must be a positive integer, got {concurrency}")
    overwrite = arguments.get("--overwrite", False)
    title_search = arguments.get("--title-search", False)

    with_fulltext_index = not arguments.get("--no-index", False)

    stats_filename: str | None = arguments.get("--stats-filename") or None
    publisher = arguments.get("--publisher") or "openZIM"
    primary_color = arguments.get("--primary-color")
    secondary_color = arguments.get("--secondary-color")
    _validate_colors(primary_color, secondary_color)

    debug = arguments.get("--debug") or False
    output_folder = Path(
        arguments.get("--output")
        or os.getenv("ZIM_OUTPUT")
        or os.getenv("GUTENBERG_OUTPUT", "./output")
    )
    cache_dir = (
        Path(arguments["--cache-dir"]).expanduser().resolve()
        if arguments.get("--cache-dir")
        else None
    )
    if cache_dir:
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            critical_error(f"Unable to create --cache-dir {cache_dir}: {exc}")
    # Calculate default UI dist path: from scraper/src/gutenberg2zim/config.py
    # go up to repo root, then to ui/dist
    default_ui_dist = Path(__file__).parent.parent.parent.parent / "ui" / "dist"
    ui_dist_raw = (
        arguments.get("--ui-dist")
        or os.getenv("ZIM_UI_DIST")
        or os.getenv("GUTENBERG_UI_DIST")
        or str(default_ui_dist)
    )
    ui_dist = Path(ui_dist_raw).resolve()

    languages = [
        x.strip().lower()
        for x in (arguments.get("--languages") or "").split(",")
        if x.strip()
    ]
    # special shortcuts for "all"
    formats: list[str]
    if arguments.get("--formats") in ["all", None]:
        formats = list(ALL_FORMATS)
    else:
        formats = list(
            {
                x.strip().lower()
                for x in (arguments.get("--formats") or "").split(",")
                if x.strip()
            }
        )

    description, long_description = compute_descriptions(
        "",
        zim_desc,
        zim_long_description,
    )

    only_books_ids: list[int] = []
    for raw_value in books_csv.split(","):
        books_value = raw_value.strip()
        if not books_value:
            continue
        parts = books_value.split("-")
        if len(parts) not in (1, 2) or not all(
            part.strip().isdigit() for part in parts
        ):
            critical_error(f"Invalid --books value: {books_value}")
        bounds = [int(part) for part in parts]
        if len(bounds) == 2:  # noqa: PLR2004
            if bounds[0] > bounds[1]:
                critical_error(f"Invalid --books range: {books_value}")
            only_books_ids.extend(range(bounds[0], bounds[1] + 1))
        else:
            only_books_ids.append(bounds[0])
    only_books_ids = list(set(only_books_ids))

    return ScrapeConfig(
        source=source.slug,
        mirror_url=mirror_url,
        output_folder=output_folder,
        cache_dir=cache_dir,
        concurrency=concurrency,
        formats=formats,
        books=[str(book_id) for book_id in only_books_ids] or None,
        languages=languages or None,
        collections=source_options.get("collections"),
        source_options=source_options,
        ui_dist=ui_dist,
        debug=debug,
        zim_file=zim_file,
        zim_name=zim_name,
        title=zim_title,
        description=description,
        long_description=long_description,
        zim_languages=(
            [lang.strip() for lang in zim_languages.split(",")]
            if (zim_languages := arguments.get("--zim-languages"))
            else None
        ),
        publisher=publisher,
        overwrite=overwrite,
        is_selection=bool(
            only_books_ids
            or source_options.get("collections")
            or source_options.get("subjects")
            or source_options.get("book_ids")
        ),
        title_search=title_search,
        with_fulltext_index=with_fulltext_index,
        stats_filename=stats_filename,
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
