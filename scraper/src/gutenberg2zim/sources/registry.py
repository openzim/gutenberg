"""Source registry: lookup of source profiles by slug.

A `SourceProfile` bundles everything the entry points (CLI/config/
orchestrator) and the core exporters need to know about a source: display
strings, ZIM metadata values, the catalog module (discovery stays
source-specific for now) and the metadata / pipeline classes.

Registration is explicit, static and eager (`SOURCES` below) - no plugin
discovery machinery, no lazy import paths. The registry is the composition
root: it is the *only* module outside `sources/<name>/` that imports source
implementations, which keeps `core/` source-free while letting the type
checker verify each profile against the port contracts (`CatalogModule`,
`MetadataPort`, `Pipeline`) at registration time.
"""

from collections.abc import Callable
from dataclasses import dataclass

from gutenberg2zim.core.pipeline import Pipeline
from gutenberg2zim.core.ports import CatalogModule, MetadataPort
from gutenberg2zim.core.utils import critical_error
from gutenberg2zim.sources.gutenberg import catalog as gutenberg_catalog
from gutenberg2zim.sources.gutenberg.metadata import GutenbergRdfMetadata
from gutenberg2zim.sources.gutenberg.pipeline import GutenbergPipeline


@dataclass(frozen=True, slots=True)
class SourceProfile:
    """Everything source-specific the source-agnostic layers need"""

    slug: str
    display_name: str
    # ZIM metadata values
    source_creator: str
    zim_tags: str
    zim_name_prefix: str
    # Human-readable source phrase used in the default ZIM description
    tagline: str
    default_mirror_url: str
    # URL path (relative to the mirror) of the catalog feed
    catalog_feed_path: str
    # The source's catalog module (discovery is still source-specific);
    # statically checked against the CatalogModule protocol
    catalog: CatalogModule
    # Constructor signatures are source-specific (sources take their own
    # extra kwargs on top of the base ones), hence Callable[..., ...]
    metadata_class: Callable[..., MetadataPort]
    pipeline_class: Callable[..., Pipeline]


GUTENBERG_PROFILE = SourceProfile(
    slug="gutenberg",
    display_name="Project Gutenberg",
    source_creator="gutenberg.org",
    zim_tags="_category:gutenberg;gutenberg",
    zim_name_prefix="gutenberg",
    tagline="the first producer of free Ebooks",
    default_mirror_url="https://gutenberg.mirror.driftle.ss",
    catalog_feed_path="/cache/epub/feeds/pg_catalog.csv.gz",
    catalog=gutenberg_catalog,
    metadata_class=GutenbergRdfMetadata,
    pipeline_class=GutenbergPipeline,
)

SOURCES: dict[str, SourceProfile] = {}


def register_source(profile: SourceProfile) -> None:
    """Register (or replace) a source profile under its slug"""
    SOURCES[profile.slug] = profile


def get_source(slug: str) -> SourceProfile:
    """Return the profile registered for `slug`, aborting on unknown slugs"""
    profile = SOURCES.get(slug)
    if profile is None:
        critical_error(
            f"Unknown source: {slug}. Available sources: {', '.join(sorted(SOURCES))}"
        )
    return profile


register_source(GUTENBERG_PROFILE)
