"""Open Textbook Library-specific command-line options."""

import sys
from typing import Any

from gutenberg2zim.core.utils import critical_error

OPTIONS = "\n".join(
    (
        "  --subjects=<subjects>           Comma-separated Open Textbook Library subjects",  # noqa: E501
        "  --otl-ids=<ids>                Exact Open Textbook Library record IDs",
        "  --list-subjects                List Open Textbook Library subjects and exit",
        "  --refresh-catalog              Refresh the Open Textbook Library CSV catalog and exit",  # noqa: E501
    )
)


def parse_options(arguments: dict[str, Any]) -> dict[str, Any]:
    if arguments.get("--lcc-shelves") is not None:
        critical_error("--lcc-shelves belongs to --source gutenberg")
    subjects = [
        item.strip()
        for item in (arguments.get("--subjects") or "").split(",")
        if item.strip()
    ]
    book_ids = [
        item.strip()
        for item in (arguments.get("--otl-ids") or "").split(",")
        if item.strip()
    ]
    if any(not book_id.isdigit() for book_id in book_ids):
        critical_error("--otl-ids must be a comma-separated list of numeric OTL IDs")
    if book_ids and arguments.get("--books"):
        critical_error("Use either --books or --otl-ids, not both")
    return {
        "subjects": subjects,
        "book_ids": book_ids,
        "list_subjects": bool(arguments.get("--list-subjects")),
        "refresh_catalog": bool(arguments.get("--refresh-catalog")),
    }


def handle_cli_action(catalog: Any, options: dict[str, Any]) -> bool:
    if options["refresh_catalog"]:
        catalog.refresh()
        return True
    if options["list_subjects"]:
        for subject in catalog.list_subjects():
            sys.stdout.write(f"{subject}\n")
        return True
    return False
