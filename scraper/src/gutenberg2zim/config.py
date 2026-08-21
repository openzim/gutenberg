"""Explicit scrape configuration.

Replaces the ad-hoc passing of CLI arguments through the call stack: the
entrypoint builds one immutable `ScrapeConfig` and hands it to the pipeline,
which forwards it (or parts of it) to the components that need it.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from zimscraperlib.image.probing import is_hex_color
from zimscraperlib.inputs import compute_descriptions

from gutenberg2zim.core.utils import ALL_FORMATS, critical_error
from gutenberg2zim.sources.registry import get_source

SUPPORTED_LCC_SHELVES = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "P",
    "PA",
    "PB",
    "PC",
    "PD",
    "PE",
    "PF",
    "PG",
    "PH",
    "PJ",
    "PK",
    "PL",
    "PM",
    "PN",
    "PQ",
    "PR",
    "PS",
    "PT",
    "PZ",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "Z",
]


@dataclass(frozen=True, slots=True)
class ScrapeConfig:
    source: str
    mirror_url: str
    output_folder: Path
    concurrency: int = 16
    formats: list[str] = field(default_factory=lambda: ["epub", "pdf", "html"])
    books: list[str] | None = None
    languages: list[str] | None = None
    collections: list[str] | None = None
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
    add_lcc_shelves: bool = False
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

    # Parse --lcc-shelves argument
    # None = not passed (don't filter by shelves, don't generate shelf pages)
    # "all" = generate all shelves
    # "P,PR,Q" = filter and generate only these shelves
    lcc_shelves_arg = arguments.get("--lcc-shelves")
    lcc_shelves: list[str] | None = None
    add_lcc_shelves = False
    if lcc_shelves_arg is not None:
        add_lcc_shelves = True
        if lcc_shelves_arg.strip().lower() == "all":
            lcc_shelves = []  # Empty list means all shelves
        else:
            requested_shelves = [
                s.strip().upper() for s in lcc_shelves_arg.split(",") if s.strip()
            ]
            invalid_shelves = set(requested_shelves) - set(SUPPORTED_LCC_SHELVES)
            if invalid_shelves:
                critical_error(
                    f"Unsupported LCC shelf code(s): "
                    f"{', '.join(sorted(invalid_shelves))}"
                )
            lcc_shelves = requested_shelves

    stats_filename: str | None = arguments.get("--stats-filename") or None
    publisher = arguments.get("--publisher") or "openZIM"
    primary_color = arguments.get("--primary-color")
    secondary_color = arguments.get("--secondary-color")
    _validate_colors(primary_color, secondary_color)

    debug = arguments.get("--debug") or False
    output_folder = Path(
        arguments.get("--output") or os.getenv("GUTENBERG_OUTPUT", "./output")
    )
    # Calculate default UI dist path: from scraper/src/gutenberg2zim/config.py
    # go up to repo root, then to ui/dist
    default_ui_dist = Path(__file__).parent.parent.parent.parent / "ui" / "dist"
    ui_dist_raw = arguments.get("--ui-dist") or os.getenv(
        "GUTENBERG_UI_DIST", str(default_ui_dist)
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
        concurrency=concurrency,
        formats=formats,
        books=[str(book_id) for book_id in only_books_ids] or None,
        languages=languages or None,
        collections=lcc_shelves,
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
        is_selection=len(only_books_ids) > 0 or len(lcc_shelves or []) > 0,
        title_search=title_search,
        add_lcc_shelves=add_lcc_shelves,
        with_fulltext_index=with_fulltext_index,
        stats_filename=stats_filename,
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
