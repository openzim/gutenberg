"""Source-specific CLI configuration validation."""

import pytest

from gutenberg2zim.config import build_scrape_config
from gutenberg2zim.core.utils import CriticalError


def test_lcc_shelves_are_rejected_for_opentextbooks():
    with pytest.raises(CriticalError, match="belongs to --source gutenberg"):
        build_scrape_config({"--source": "opentextbooks", "--lcc-shelves": "all"})


def test_subjects_are_rejected_for_gutenberg():
    with pytest.raises(CriticalError, match="belongs to --source opentextbooks"):
        build_scrape_config({"--source": "gutenberg", "--subjects": "Mathematics"})


def test_subjects_are_stored_for_opentextbooks():
    config = build_scrape_config(
        {
            "--source": "opentextbooks",
            "--subjects": "Mathematics, Business - Accounting",
        }
    )

    assert config.source_options["subjects"] == ["Mathematics", "Business - Accounting"]


def test_otl_ids_are_stored_for_opentextbooks():
    config = build_scrape_config({"--source": "opentextbooks", "--otl-ids": "42,108"})

    assert config.source_options["book_ids"] == ["42", "108"]


def test_otl_ids_and_books_cannot_be_combined():
    with pytest.raises(CriticalError, match="either --books or --otl-ids"):
        build_scrape_config(
            {"--source": "opentextbooks", "--books": "1-5", "--otl-ids": "42"}
        )


def test_otl_only_arguments_are_rejected_for_gutenberg():
    with pytest.raises(CriticalError, match="--list-subjects belongs"):
        build_scrape_config({"--source": "gutenberg", "--list-subjects": True})


def test_source_neutral_environment_variables_configure_output_and_ui(
    monkeypatch, tmp_path
):
    output = tmp_path / "output"
    ui_dist = tmp_path / "ui"
    monkeypatch.setenv("ZIM_OUTPUT", str(output))
    monkeypatch.setenv("ZIM_UI_DIST", str(ui_dist))

    config = build_scrape_config({"--source": "opentextbooks"})

    assert config.output_folder == output
    assert config.ui_dist == ui_dist.resolve()


def test_cache_dir_is_opt_in_and_resolved(tmp_path):
    assert build_scrape_config({"--source": "gutenberg"}).cache_dir is None

    cache_dir = tmp_path / "cache"
    config = build_scrape_config(
        {"--source": "opentextbooks", "--cache-dir": str(cache_dir)}
    )

    assert config.cache_dir == cache_dir.resolve()
    assert cache_dir.is_dir()
