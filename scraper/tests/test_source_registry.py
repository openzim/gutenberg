"""Tests for static source-profile registration."""

from dataclasses import replace

import pytest

from gutenberg2zim.core.ports import CatalogPort
from gutenberg2zim.sources import registry
from gutenberg2zim.sources.opentextbooks.catalog import OpenTextbookLibraryCatalog
from gutenberg2zim.sources.opentextbooks.metadata import OpenTextbookLibraryMetadata
from gutenberg2zim.sources.registry import get_source
from gutenberg2zim.sources.wikisource.catalog import WikisourceCatalog
from gutenberg2zim.sources.wikisource.metadata import WikisourceMetadata


@pytest.fixture
def isolated_registry(monkeypatch):
    monkeypatch.setattr(registry, "SOURCES", {})
    monkeypatch.setattr(registry, "SOURCE_ALIASES", {})
    return registry


def _profile(slug: str, aliases: tuple[str, ...]):
    return replace(
        registry.GUTENBERG_PROFILE,
        slug=slug,
        aliases=aliases,
        cli_options={},
    )


@pytest.mark.parametrize(
    ("source_name", "source_slug"),
    (
        ("PG", "gutenberg"),
        ("pg", "gutenberg"),
        ("OTL", "opentextbooks"),
        ("WS", "wikisource"),
        ("ws", "wikisource"),
    ),
)
def test_source_short_names_resolve_case_insensitively(source_name, source_slug):
    assert get_source(source_name).slug == source_slug


def test_register_source_rejects_slug_that_conflicts_with_an_alias(isolated_registry):
    isolated_registry.register_source(_profile("first", ("other",)))

    with pytest.raises(ValueError, match="Source slug other conflicts"):
        isolated_registry.register_source(_profile("other", ()))


def test_replacing_source_removes_its_previous_aliases(isolated_registry):
    isolated_registry.register_source(_profile("first", ("old",)))
    replacement = _profile("first", ("new",))

    isolated_registry.register_source(replacement)

    assert "old" not in isolated_registry.SOURCE_ALIASES
    assert isolated_registry.get_source("new") is replacement


def test_opentextbooks_profile_is_registered_with_its_json_adapters():
    profile = get_source("opentextbooks")

    assert profile.display_name == "Open Textbook Library"
    assert profile.default_mirror_url == "https://open.umn.edu/opentextbooks"
    assert profile.catalog is OpenTextbookLibraryCatalog
    assert isinstance(profile.catalog, type)
    assert issubclass(profile.catalog, CatalogPort)
    assert profile.metadata_class is OpenTextbookLibraryMetadata
    assert profile.pipeline_class is not None


def test_wikisource_profile_is_registered_with_its_opds_adapters():
    profile = get_source("wikisource")

    assert profile.display_name == "Wikisource"
    assert profile.default_mirror_url == "https://ws-export.wmcloud.org"
    assert profile.catalog is WikisourceCatalog
    assert isinstance(profile.catalog, type)
    assert issubclass(profile.catalog, CatalogPort)
    assert profile.metadata_class is WikisourceMetadata
    assert profile.pipeline_class is not None
