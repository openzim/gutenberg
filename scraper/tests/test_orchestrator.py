"""Tests for scrape orchestration resource lifetimes."""

from unittest.mock import MagicMock, patch

import pytest

from gutenberg2zim.config import ScrapeConfig
from gutenberg2zim.orchestrator import run_scrape


class FailingCatalog:
    def __init__(self, *_args, **_kwargs):
        raise RuntimeError("catalog setup failed")


def test_closes_download_engine_when_catalog_construction_fails(tmp_path):
    engine = MagicMock(name="engine")
    profile = MagicMock(name="profile", catalog=FailingCatalog)
    config = ScrapeConfig(
        source="test",
        mirror_url="https://example.test",
        output_folder=tmp_path,
    )

    with (
        patch("gutenberg2zim.orchestrator.DownloadEngine", return_value=engine),
        patch("gutenberg2zim.orchestrator.get_source", return_value=profile),
        patch("gutenberg2zim.orchestrator.i18n.setup_i18n"),
        pytest.raises(RuntimeError, match="catalog setup failed"),
    ):
        run_scrape(config)

    engine.close.assert_called_once_with()
