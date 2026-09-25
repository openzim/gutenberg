"""Regression checks for Zimfarm recipe options."""

import json
from pathlib import Path

DEFINITION_PATH = Path(__file__).parents[2] / "offliner-definition.json"


def test_recipe_defines_supported_sources_and_source_specific_filters():
    definition = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))
    flags = definition["flags"]

    assert flags["source"] == {
        "type": "string-enum",
        "required": False,
        "title": "Source",
        "description": (
            "Book source to scrape. Source-specific options are shown below; do not "
            "combine options from different sources."
        ),
        "choices": [
            {
                "title": "Project Gutenberg",
                "value": "gutenberg",
                "dependents": ["lcc_shelves", "with_author_details"],
            },
            {
                "title": "Open Textbook Library",
                "value": "opentextbooks",
                "dependents": ["subjects", "otl_ids"],
            },
            {
                "title": "Wikisource",
                "value": "wikisource",
                "dependents": [],
            },
        ],
    }
    assert {"lcc_shelves", "subjects", "otl_ids", "with_author_details"}.issubset(
        flags
    )


def test_recipe_uses_enum_choices_for_supported_formats():
    definition = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))

    assert definition["flags"]["formats"]["type"] == "list-of-string-enum"
    assert [
        choice["value"] for choice in definition["flags"]["formats"]["choices"]
    ] == ["epub", "html", "pdf"]


def test_recipe_exposes_custom_zim_tags():
    definition = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))

    assert definition["flags"]["zim_tags"] == {
        "type": "string",
        "required": False,
        "title": "ZIM Tags",
        "description": (
            "Semicolon-separated ZIM tags. Overrides the selected source's default "
            "tags; for example: _category:medical;gutenberg."
        ),
    }
    assert {"metadata": "Tags", "flag": "zim_tags"} in definition["zimMetadata"]


def test_with_author_details_is_a_pg_only_boolean_flag():
    definition = json.loads(DEFINITION_PATH.read_text(encoding="utf-8"))
    flags = definition["flags"]

    assert flags["with_author_details"] == {
        "type": "boolean",
        "required": False,
        "title": "With author details",
        "description": (
            "Add author details (biography and portrait) fetched from the English "
            "Wikipedia. Project Gutenberg source only for now."
        ),
    }

    gutenberg_choices = [
        choice
        for choice in flags["source"]["choices"]
        if choice["value"] == "gutenberg"
    ]
    assert "with_author_details" in gutenberg_choices[0]["dependents"]
    for choice in flags["source"]["choices"]:
        if choice["value"] != "gutenberg":
            assert "with_author_details" not in choice["dependents"]
