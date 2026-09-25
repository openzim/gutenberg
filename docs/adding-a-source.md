# Adding a New Source

[PR #525](https://github.com/openzim/gutenberg/pull/525) introduced the Open
Textbook Library (OTL) and the source-agnostic architecture. A candidate such
as [issue #527](https://github.com/openzim/gutenberg/issues/527) should be
integrated through the same boundaries. In particular, investigate whether a
standard such as OPDS is consistent enough to justify a reusable adapter; do
not assume that two feeds with the same format have identical semantics.

## Architecture and ownership

The normal data flow is:

```text
CLI/config -> SourceProfile -> CatalogPort -> WorkRef
           -> Pipeline workers -> MetadataPort -> Work
           -> FormatResolverPort/DownloadEngine -> ZimAssembler
           -> core indexes/exporters -> shared UI
```

Code under `core/` must not import a source implementation, check a source
slug, or use source vocabulary such as LCC shelves or subjects. A source owns
its URLs, API payloads, identifiers, metadata interpretation, filters, HTML
mirroring, and source-specific transformations under `sources/<source>/`.
`sources/registry.py` is the only composition root allowed to import all source
implementations.

A typical source package contains:

```text
sources/<source>/
  __init__.py
  catalog.py       # discovery and source-side filtering
  cli.py           # source-specific CLI declarations and validation
  metadata.py      # WorkRef -> source-agnostic Work mapping
  resolver.py      # Work + requested format -> DownloadRequest
  pipeline.py      # processing and exporting one work
```

Add optional modules such as `covers.py`, `html_mirror.py`, or
`invalid_urls.py` only when the source needs them. Do not create empty plugin
modules pre-emptively.

## 1. Model the source as works

Read `core/models.py` before writing an adapter. Map source data into:

- `Work`: stable source ID, title, creators, languages, license, formats,
  collections, description, publication date, source URL, and popularity;
- `Creator`: a stable creator ID and display/sort metadata;
- `Format`: source format name, media type, URL/path, and optional size;
- `CollectionRef`: any source grouping (shelf, subject, category, series, etc.);
- `Cover`: source/local cover information.

Core and UI code call these items **works**, **creators**, and **collections**.
Keep source words such as “book”, “shelf”, or “subject” inside the source and
its locale namespace. Creator and collection IDs must be stable across runs;
do not derive a different creator ID for every work.

`Work.popularity` is the raw numeric ranking signal supplied by the source
(downloads, page views, review score, etc.). Core derives the zero-to-three
`Work.flames` value after processing, so sources must not calculate flames.
Leave popularity as `None` when no defensible metric exists and do not label an
arbitrary work “Most popular” in that source's messages.

Use `Work.extra`, `Creator.extra`, and `CollectionRef.extra` for data that is
strictly source-internal. If shared exporters or the UI need a concept, model
it explicitly and source-agnostically instead of teaching core about one
source's payload keys.

## 2. Implement catalog discovery

New sources should implement `CatalogPort.discover(CatalogFilters)` and return
lightweight `WorkRef` objects. The catalog runs before the worker pool and is
responsible for:

- fetching/parsing the source catalog;
- applying language, format, collection, positional `--books`, and custom
  source filters;
- returning deterministic, deduplicated refs in a stable order;
- putting only metadata fallbacks needed later into `WorkRef.extra`.

Class-based catalogs are constructed with the shared `DownloadEngine` plus
`base_url`, `cache_dir`, and `refresh_catalog`. Accept unused constructor
arguments explicitly or through `**_` so the orchestrator can construct the
adapter consistently.

```python
class ExampleCatalog(CatalogPort):
    def __init__(self, engine: DownloadEngine, base_url: str, **_: object):
        self.engine = engine
        self.base_url = base_url.rstrip("/")

    def discover(self, filters: CatalogFilters) -> Iterable[WorkRef]:
        # Fetch, filter, deduplicate, and yield stable lightweight refs.
        ...
```

`--books` means positions in the source's already-eligible catalog. If a
source also needs exact record IDs, add a clearly named custom option as OTL
does with `--otl-ids`; do not silently change the meaning of `--books`.

Persistent catalog caching is opt-in through `--cache-dir`. With no cache
directory, keep catalog data in memory and leave no files in the output
directory. A refresh-only action must fail fast when no cache directory is
provided.

## 3. Map full metadata

Implement `MetadataPort.fetch(refs)` in `metadata.py`. It may fetch one record
per ref (OTL) or map metadata already carried by the catalog (Wikisource), but
it must yield `Work` instances and must use the shared `DownloadEngine` for
HTTP requests.

```python
class ExampleMetadata(MetadataPort):
    def __init__(self, base_url: str, *, engine: DownloadEngine, **_: object):
        self.engine = engine
        self.base_url = base_url.rstrip("/")

    def fetch(self, refs: Iterable[WorkRef]) -> Iterable[Work]:
        for ref in refs:
            yield Work(id=ref.id, source="example", title="...", ...)
```

Normalize source data here:

- language codes expected by core and the UI;
- human-readable license labels rather than raw source URLs;
- stable creator and collection IDs;
- canonical source URLs and valid media types;
- a meaningful popularity signal, if available.

Metadata caching is also opt-in through `--cache-dir`. Cache source metadata,
not optimized covers or book assets, unless a separate design explicitly
justifies and invalidates such a cache. Treat malformed cached data as a cache
miss, and use atomic writes for cache files.

## 4. Resolve requested formats

Implement `FormatResolverPort.resolve(work, format_name)` when URLs cannot be
computed directly in the pipeline. It translates canonical requested formats
(`epub`, `pdf`, and `html`) into a `DownloadRequest` or returns `None` when the
work does not provide that format.

```python
class ExampleFormatResolver(FormatResolverPort):
    def resolve(self, work: Work, format_name: str) -> DownloadRequest | None:
        ...
```

`RewriterPort` is available when a source benefits from a dedicated HTML
transformation object. The source pipeline still owns when that rewriter is
invoked and which source policy it applies.

Do not trust extensions, HTTP content types, or landing-page URLs alone.
Resolve candidate URLs according to source behavior, download them, and then
validate their actual content. Record missing or rejected requested formats in
`work.extra["unsupported_formats"]`; core exporters use this list to avoid
advertising buttons for files that were not added to the ZIM.

## 5. Implement per-work processing

Subclass `core.pipeline.Pipeline` and implement `process_ref(ref)`. The method
owns the complete lifecycle of one work:

1. fetch/map metadata;
2. resolve and download requested formats;
3. reject invalid or incomplete editions;
4. optimize supported assets;
5. add valid editions and covers through `ZimAssembler`;
6. mark unavailable formats;
7. add the work to `WorkStore` only after at least one requested edition was
   successfully exported.

```python
class ExamplePipeline(Pipeline):
    def __init__(self, *, engine: DownloadEngine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self.resolver = ExampleFormatResolver()

    def process_ref(self, ref: WorkRef) -> None:
        # Process exactly one ref; Pipeline.run() supplies concurrency.
        ...
```

Use `setup()` for shared assets that must be exported once before workers
start. Override `run()` only for bounded resource setup/cleanup, and always
delegate to `super().run()` inside `try/finally`.

The base pipeline already provides:

- `--concurrency` parallelism across works;
- retry of transient ZIM write contention;
- progress reporting and per-work failure isolation;
- flame computation from `Work.popularity`;
- author/collection indexes and search entries;
- JSON data, No-JS pages, and shared UI configuration exports.

Sources should not call `IndexBuilder` or the JSON, search, and No-JS
exporters directly; the base pipeline runs them once after all workers finish.

Do not create another top-level worker pool. `process_ref()` is already called
inside the shared pool, and `DownloadEngine` supplies a persistent HTTP session
per worker thread. Any nested concurrency (for example, parallel cover fetches)
must be small, bounded, and shut down in `finally`. Remember that
`fetch_bytes()` holds the complete response in memory, so high concurrency and
large editions can multiply memory use.

## 6. Reuse core services

Before adding source-local helpers, check the facilities already exposed by
`core/`:

- `DownloadEngine.fetch_bytes()`: retrying in-memory HTTP GET using
  thread-local sessions and the scraper User-Agent;
- `DownloadEngine.download()`: streamed, atomic download to an explicit target
  or opt-in cache, returning a `DownloadResult`;
- `DownloadEngine.content_type()`: best-effort HEAD probe; downloaded content
  must still be validated;
- `is_fatal_http_error()`: distinguishes permanent 4xx failures from retryable
  failures and HTTP 429;
- `content_validation.is_html_document()` and `is_valid_book_file()`:
  source-neutral PDF/EPUB validation;
- `covers.extract_cover()`: WebP cover extraction from an EPUB declaration or
  the first PDF page;
- `epub_optimizer.optimize_epub_bytes()`: in-memory EPUB optimization that
  preserves ZIP/EPUB invariants and keeps embedded JPEG/PNG formats; pass a
  source-owned document callback only for source-specific XHTML/NCX cleanup;
- `ImageProcessor`: JPEG/PNG-to-WebP conversion and output naming for covers
  and mirrored HTML assets;
- `rewrite_html_image_references()`: update HTML references after WebP
  conversion;
- `link_rewriter.replacement_link()`: rewrite a relative sibling-page link to
  the ZIM naming convention while preserving fragments;
- `export_html_reader_control_assets()`: shared info, EPUB/PDF download, and
  scroll-to-top controls for offline HTML editions;
- `ZimAssembler.add_item_for()` and `add_alias()`: serialized, thread-safe ZIM
  writes and aliases;
- naming helpers in `core.utils`: `archive_name_for()`, `article_name_for()`,
  `collection_key()`, and `requested_formats()`;
- `atomic_write_text()` and `critical_error()`: atomic source-cache updates and
  consistent fatal CLI errors;
- helpers in `core.language`: language-name resolution and ZIM language
  metadata;
- `WorkStore`: thread-safe storage keyed by `(source, work ID)`.

The orchestrator owns `ZimAssembler.start()`/`finish()`, progress totals, the
top-level `parallel_map()`, `IndexBuilder`, UI/No-JS/search exporters, and i18n
setup. Source code should consume their results through `Pipeline`, not run a
second finalization path.

For EPUBs, do not convert embedded JPEG/PNG files to WebP because manifest and
document references must remain valid. For standalone covers and mirrored HTML
assets, use `ImageProcessor`, store the result with a `.webp` path and
`image/webp` MIME type, and rewrite every reference. Do not add optimized-asset
caching as an incidental part of a new source.

An HTML edition is complete only when all required pages, stylesheets, images,
fonts, and internal links are available offline. A publisher landing page is
not an HTML edition. HTML-capable sources should export the shared reader
controls, retain download buttons only for formats actually stored in the ZIM,
and test navigation without network access.

## 7. Define source-specific CLI options

Declare custom arguments in `sources/<source>/cli.py`:

```python
CLI_OPTIONS = {
    "--example-filter": "  --example-filter=<value>       Description",
}

def parse_options(arguments: dict[str, Any]) -> dict[str, Any]:
    # Normalize and fail fast on invalid or conflicting values.
    return {"example_filter": ...}

def handle_cli_action(catalog: Any, options: dict[str, Any]) -> bool:
    # Perform list/refresh-and-exit actions; False continues the scrape.
    return False
```

The core CLI assembles all declared options and centrally rejects options that
belong to another source. Option names must be unique across registered
sources. Put an option in the global CLI only when its meaning and validation
are genuinely shared by every source.

Expose source-specific actions and filters through `source_options`; do not add
`if source == ...` branches to `cli.py`, `config.py`, or `orchestrator.py`.

## 8. Register the source profile

Add one `SourceProfile` in `sources/registry.py` and register it. Use a lowercase
canonical slug and a short, case-insensitive alias (normally the uppercase
initials of the source name). The registry validates alias and custom CLI
option uniqueness.

The profile supplies:

- UI locale namespace and human-readable source name;
- ZIM creator, default tags, name prefix, tagline, and description;
- collection label/icon style;
- default source/mirror URL;
- catalog, metadata, and pipeline implementations;
- CLI parser/action hooks;
- source-specific constructor options for metadata and pipeline objects.

```python
EXAMPLE_PROFILE = SourceProfile(
    slug="example",
    aliases=("EX",),
    locale_namespace="example",
    display_name="Example Library",
    source_creator="example.org",
    zim_tags="_category:books;example",
    zim_name_prefix="example",
    tagline="a library of example works",
    source_description="Example source description.",
    collection_label="Collections",
    collection_icon_style="classification",
    default_mirror_url="https://example.org",
    catalog_feed_path="",
    catalog=ExampleCatalog,
    cli_options=example_cli.CLI_OPTIONS,
    parse_cli_options=example_cli.parse_options,
    handle_cli_action=example_cli.handle_cli_action,
    pipeline_options=lambda _mirror_url, _cache_dir: {},
    metadata_options=lambda _cache_dir: {},
    metadata_class=ExampleMetadata,
    pipeline_class=ExamplePipeline,
)

register_source(EXAMPLE_PROFILE)
```

Use the canonical slug, not the alias, in Zimfarm and generated metadata. A
class-based catalog normally uses an empty `catalog_feed_path`; that field
exists for Gutenberg's legacy CSV catalog adapter.

## 9. Add locale and UI support

Each locale file contains a `common` namespace plus source namespaces. For a
new source, add its complete namespace to **only** `locales/en.json` and
`locales/qqq.json`. Never manually add new messages to translated locale files.

Source messages customize labels such as the About page, collection wording,
featured-work wording, metadata defaults, and footer text. Every key rendered
unconditionally by the UI must exist; validate the About page in particular.
Do not solve missing source capabilities by publishing misleading labels such
as “Most popular” when the source has no popularity signal.

When adding a reusable UI concept:

1. use source-neutral names such as `work` and `collection` in Python,
   TypeScript, routes, and component names;
2. add the shared message below `common` in `en.json` and document it in
   `qqq.json`;
3. add source wording below the source namespace only when it actually differs;
4. update Pydantic schemas, JSON exporters, TypeScript types, and UI tests
   together if the serialized contract changes.

If a source cannot provide authors, collections, popularity, or a format, the
UI must hide or neutrally represent that capability rather than showing empty
or false sections. A reusable capability gap is a valid reason to extend core
and the UI source-agnostically.

If the source adds content language codes not already bundled for display,
update `ui/scripts/generate-language-names.js` using a source-agnostic union of
catalog language codes. Do not introduce a second source-specific language-name
generator.

## 10. Update Zimfarm and documentation

Add the canonical source to the `source` enum in `offliner-definition.json`.
Declare its custom flags as dependents and document format, language, caching,
and selection requirements. Zimfarm cannot infer this information from the
Python registry.

Also update:

- `README.md` with a minimal scrape command and source-specific behavior;
- `CHANGELOG.md`;
- scraper package keywords when appropriate;
- screenshots or a small sample ZIM when UI behavior changes.

## 11. Test the complete integration

At minimum, add focused tests for:

- catalog parsing, filtering, stable ordering, and deduplication;
- metadata mapping into `Work`, including missing/malformed fields;
- format resolution and invalid/landing-page responses;
- pipeline success, partial formats, total failure, covers, optimization, and
  `unsupported_formats`;
- source registration, aliases, CLI validation, locales, and
  `offliner-definition.json`;
- any shared core behavior introduced by the source.

Add a representative one-work integration ZIM to both
`.github/workflows/Tests.yaml` and `.github/workflows/DailyTests.yaml`, validate
it with `zimcheck`, and extend `scraper/tests-integration/`. Keep it reliably
below five minutes. A mocked unit suite does not verify an external catalog or
download contract.

Exercise the source locally with a small selection, inspect the resulting ZIM
in Kiwix, and verify desktop and mobile UI behavior. Check covers, authors,
licenses, collections, format buttons/readers, About content, language labels,
No-JS pages, and offline navigation.

Before submitting, run:

```bash
cd scraper
hatch run test:run
hatch run lint:all
hatch run check:all
gutenberg2zim-validate-i18n

cd ../ui
npm run type-check
npm run lint-check
npm run format-check
npm run test:unit
npm run test:integration
npm run build
```

## When core should change

A new source should normally require changes only in its source package, the
registry, locales, Zimfarm definition, documentation, and tests. Change core
only when the abstraction is useful to multiple sources and its API can be
expressed without source names or source conditionals.

Good core changes include reusable validation, download behavior, cover or
EPUB optimization, a new domain field needed consistently downstream, or a
capability flag shared by multiple sources. Prefer a source callback when core
owns an algorithm but a source owns a transformation.

Before modifying core:

1. confirm the behavior is not merely source policy;
2. define or extend a source-neutral model/port/helper;
3. keep source imports out of `core/`;
4. preserve behavior for existing sources;
5. add regression tests for every affected source;
6. update schemas, TypeScript types, exporters, locales, and documentation when
   the public JSON contract changes.

Do not generalize a protocol prematurely. For example, issue #527 may justify
a reusable OPDS catalog only after comparing multiple feeds for pagination,
metadata fields, acquisition relations, authentication, covers, identifiers,
and update semantics.
