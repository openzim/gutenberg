"""Wikisource-specific command-line options.

Language selection uses the shared ``--languages`` option (Wikisource is
organised per language), so this source adds no options of its own.
"""

from typing import Any

CLI_OPTIONS: dict[str, str] = {}


def parse_options(_arguments: dict[str, Any]) -> dict[str, Any]:
    return {}


def handle_cli_action(_catalog: Any, _options: dict[str, Any]) -> bool:
    return False
