"""Project Gutenberg-specific command-line options."""

from typing import Any

from gutenberg2zim.core.utils import critical_error

SUPPORTED_LCC_SHELVES = {
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
}

OPTIONS = (
    "--lcc-shelves=<shelves>         Comma-separated LCC shelf codes to include "
    "(e.g., P,PR,Q). Use 'all' for every shelf"
)


def parse_options(arguments: dict[str, Any]) -> dict[str, Any]:
    for option in ("--subjects", "--otl-ids", "--list-subjects", "--refresh-catalog"):
        if arguments.get(option):
            critical_error(f"{option} belongs to --source opentextbooks")
    value = arguments.get("--lcc-shelves")
    if value is None:
        return {}
    if value.strip().lower() == "all":
        return {"collections": []}
    collections = [item.strip().upper() for item in value.split(",") if item.strip()]
    invalid = set(collections) - SUPPORTED_LCC_SHELVES
    if invalid:
        critical_error(f"Unsupported LCC shelf code(s): {', '.join(sorted(invalid))}")
    return {"collections": collections}


def handle_cli_action(_catalog: Any, _options: dict[str, Any]) -> bool:
    return False
