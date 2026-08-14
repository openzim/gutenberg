"""Tests for static source-profile registration."""

from gutenberg2zim.core.ports import CatalogPort
from gutenberg2zim.sources.opentextbooks.catalog import OpenTextbookLibraryCatalog
from gutenberg2zim.sources.opentextbooks.metadata import OpenTextbookLibraryMetadata
from gutenberg2zim.sources.registry import get_source


def test_opentextbooks_profile_is_registered_with_its_json_adapters():
    profile = get_source("opentextbooks")

    assert profile.display_name == "Open Textbook Library"
    assert profile.default_mirror_url == "https://open.umn.edu/opentextbooks"
    assert profile.catalog is OpenTextbookLibraryCatalog
    assert isinstance(profile.catalog, type)
    assert issubclass(profile.catalog, CatalogPort)
    assert profile.metadata_class is OpenTextbookLibraryMetadata
    assert profile.pipeline_class is not None
