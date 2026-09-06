"""Source registry: lookup of source profiles by slug.

A `SourceProfile` bundles everything the entry points (CLI/config/
orchestrator) and the core exporters need to know about a source: display
strings, ZIM metadata values, the catalog adapter and the metadata / pipeline
classes.

Registration is explicit, static and eager (`SOURCES` below) - no plugin
discovery machinery, no lazy import paths. The registry is the composition
root: it is the *only* module outside `sources/<name>/` that imports source
implementations, which keeps `core/` source-free while letting the type
checker verify each profile against the port contracts at registration time.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gutenberg2zim.core.pipeline import Pipeline
from gutenberg2zim.core.ports import MetadataPort
from gutenberg2zim.core.utils import critical_error
from gutenberg2zim.sources.gutenberg import catalog as gutenberg_catalog
from gutenberg2zim.sources.gutenberg import cli as gutenberg_cli
from gutenberg2zim.sources.gutenberg.metadata import GutenbergRdfMetadata
from gutenberg2zim.sources.gutenberg.pipeline import GutenbergPipeline
from gutenberg2zim.sources.opentextbooks import cli as opentextbooks_cli
from gutenberg2zim.sources.opentextbooks.catalog import OpenTextbookLibraryCatalog
from gutenberg2zim.sources.opentextbooks.metadata import OpenTextbookLibraryMetadata
from gutenberg2zim.sources.opentextbooks.pipeline import OpenTextbookLibraryPipeline


@dataclass(frozen=True, slots=True)
class SourceProfile:
    """Everything source-specific the source-agnostic layers need"""

    slug: str
    aliases: tuple[str, ...]
    locale_namespace: str
    display_name: str
    # ZIM metadata values
    source_creator: str
    zim_tags: str
    zim_name_prefix: str
    # Human-readable source phrase used in the default ZIM description
    tagline: str
    source_description: str
    collection_label: str
    collection_icon_style: str
    default_mirror_url: str
    # URL path (relative to the mirror) of the catalog feed
    catalog_feed_path: str
    catalog: Any
    cli_options: Mapping[str, str]
    parse_cli_options: Callable[[dict[str, Any]], dict[str, Any]]
    handle_cli_action: Callable[[Any, dict[str, Any]], bool]
    pipeline_options: Callable[[str, Path | None], dict[str, Any]]
    metadata_options: Callable[[Path | None], dict[str, Any]]
    # Constructor signatures are source-specific (sources take their own
    # extra kwargs on top of the base ones), hence Callable[..., ...]
    metadata_class: Callable[..., MetadataPort]
    pipeline_class: Callable[..., Pipeline]


GUTENBERG_PROFILE = SourceProfile(
    slug="gutenberg",
    aliases=("PG",),
    locale_namespace="gutenberg",
    display_name="Project Gutenberg",
    source_creator="gutenberg.org",
    zim_tags="_category:gutenberg;gutenberg",
    zim_name_prefix="gutenberg",
    tagline="the first producer of free eBooks",
    source_description="A library of free ebooks from Project Gutenberg.",
    collection_label="LCC Shelves",
    collection_icon_style="classification",
    default_mirror_url="https://aleph.pglaf.org",
    catalog_feed_path="/cache/epub/feeds/pg_catalog.csv.gz",
    catalog=gutenberg_catalog,
    cli_options=gutenberg_cli.CLI_OPTIONS,
    parse_cli_options=gutenberg_cli.parse_options,
    handle_cli_action=gutenberg_cli.handle_cli_action,
    pipeline_options=lambda mirror_url, _cache_dir: {"mirror_url": mirror_url},
    metadata_options=lambda _cache_dir: {},
    metadata_class=GutenbergRdfMetadata,
    pipeline_class=GutenbergPipeline,
)

OPEN_TEXTBOOK_LIBRARY_PROFILE = SourceProfile(
    slug="opentextbooks",
    aliases=("OTL",),
    locale_namespace="opentextbooks",
    display_name="Open Textbook Library",
    source_creator="open.umn.edu",
    zim_tags="_category:education;opentextbooks",
    zim_name_prefix="opentextbooks",
    tagline="free, peer-reviewed, openly licensed textbooks",
    source_description="Free, peer-reviewed, openly licensed textbooks.",
    collection_label="Subjects",
    collection_icon_style="subject",
    default_mirror_url="https://open.umn.edu/opentextbooks",
    catalog_feed_path="",
    catalog=OpenTextbookLibraryCatalog,
    cli_options=opentextbooks_cli.CLI_OPTIONS,
    parse_cli_options=opentextbooks_cli.parse_options,
    handle_cli_action=opentextbooks_cli.handle_cli_action,
    pipeline_options=lambda _mirror_url, cache_dir: {"cache_dir": cache_dir},
    metadata_options=lambda cache_dir: {"cache_dir": cache_dir},
    metadata_class=OpenTextbookLibraryMetadata,
    pipeline_class=OpenTextbookLibraryPipeline,
)

SOURCES: dict[str, SourceProfile] = {}
SOURCE_ALIASES: dict[str, SourceProfile] = {}


def register_source(profile: SourceProfile) -> None:
    """Register (or replace) a source profile under its slug"""
    source_key = profile.slug.casefold()
    alias_keys = tuple(alias.casefold() for alias in profile.aliases)
    if source_key != profile.slug:
        raise ValueError(f"Source slug must be lowercase: {profile.slug}")
    if len(alias_keys) != len(set(alias_keys)):
        raise ValueError(f"Source {profile.slug} declares duplicate aliases")

    duplicate_options = set(profile.cli_options).intersection(
        option
        for existing_profile in SOURCES.values()
        if existing_profile.slug != profile.slug
        for option in existing_profile.cli_options
    )
    if duplicate_options:
        raise ValueError(
            f"Source {profile.slug} reuses custom CLI option(s): "
            f"{', '.join(sorted(duplicate_options))}"
        )

    alias_owner = SOURCE_ALIASES.get(source_key)
    if alias_owner and alias_owner.slug != profile.slug:
        raise ValueError(
            f"Source slug {profile.slug} conflicts with source alias "
            f"registered for {alias_owner.slug}"
        )
    for alias, alias_key in zip(profile.aliases, alias_keys, strict=True):
        if alias_key == source_key:
            raise ValueError(
                f"Source {profile.slug} cannot use its own slug as an alias"
            )
        slug_owner = SOURCES.get(alias_key)
        if slug_owner and slug_owner.slug != profile.slug:
            raise ValueError(
                f"Source alias {alias} conflicts with source slug {slug_owner.slug}"
            )
        existing_profile = SOURCE_ALIASES.get(alias_key)
        if existing_profile and existing_profile.slug != profile.slug:
            raise ValueError(
                f"Source alias {alias} is already registered for "
                f"{existing_profile.slug}"
            )

    for alias_key, existing_profile in tuple(SOURCE_ALIASES.items()):
        if existing_profile.slug == profile.slug:
            del SOURCE_ALIASES[alias_key]
    SOURCES[source_key] = profile
    for alias_key in alias_keys:
        SOURCE_ALIASES[alias_key] = profile


def get_source(slug: str) -> SourceProfile:
    """Return the profile registered for a source slug or case-insensitive alias."""
    source_key = slug.casefold()
    profile = SOURCES.get(source_key) or SOURCE_ALIASES.get(source_key)
    if profile is None:
        available_sources = ", ".join(
            (
                f"{registered.slug} ({', '.join(registered.aliases)})"
                if registered.aliases
                else registered.slug
            )
            for registered in SOURCES.values()
        )
        critical_error(
            f"Unknown source: {slug}. Available sources: {available_sources}"
        )
    return profile


register_source(GUTENBERG_PROFILE)
register_source(OPEN_TEXTBOOK_LIBRARY_PROFILE)
