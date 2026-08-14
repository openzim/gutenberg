"""Tests for sources.opentextbooks.metadata with a stubbed download engine."""

import json
from pathlib import Path

import requests

from gutenberg2zim.core.download_engine import DownloadEngine
from gutenberg2zim.core.ports import WorkRef
from gutenberg2zim.sources.opentextbooks.metadata import OpenTextbookLibraryMetadata

BASE = "https://open.umn.edu/opentextbooks"

RECORD = {
    "id": 10,
    "title": "Calculus",
    "language": "eng",
    "license": "Attribution-NonCommercial-ShareAlike",
    "description": "A calculus textbook.",
    "rating": "4",
    "textbook_reviews_count": 7,
    "url": f"{BASE}/textbooks/calculus",
    "copyright_year": 2016,
    "isbn13": "9781938168068",
    "contributors": [
        {
            "id": 2184,
            "contribution": "Author",
            "primary": True,
            "corporate": False,
            "first_name": "Gilbert",
            "middle_name": None,
            "last_name": "Strang",
        },
        {
            "id": 99,
            "contribution": "Editor",
            "primary": False,
            "corporate": False,
            "first_name": "Ed",
            "middle_name": None,
            "last_name": "Itor",
        },
    ],
    "subjects": [{"id": 5, "name": "Mathematics"}],
    "formats": [
        {"id": 1, "type": "PDF", "url": "https://example.org/calculus.pdf"},
        {"id": 2, "type": "Online", "url": "https://example.org/calculus"},
    ],
}


class StubEngine(DownloadEngine):
    """Serves canned records keyed by URL, or raises like a failed request"""

    def __init__(
        self, pages: dict[str, bytes], errors: dict[str, Exception] | None = None
    ):
        self._pages = pages
        self._errors = errors or {}

    def fetch_bytes(self, url: str) -> bytes:
        if url in self._errors:
            raise self._errors[url]
        return self._pages[url]


def _record_payload(record: dict = RECORD) -> bytes:
    return json.dumps({"data": record}).encode()


def _metadata_with(
    pages: dict[str, bytes],
    errors: dict[str, Exception] | None = None,
    cache_dir: Path | None = None,
):
    return OpenTextbookLibraryMetadata(
        engine=StubEngine(pages, errors), cache_dir=cache_dir
    )


def _ref(textbook_id: str) -> WorkRef:
    return WorkRef(id=textbook_id, source="opentextbooks", extra={})


def test_fetch_maps_record_to_work():
    metadata = _metadata_with({f"{BASE}/textbooks/10.json": _record_payload()})

    (work,) = metadata.fetch([_ref("10")])

    assert work.id == "10"
    assert work.source == "opentextbooks"
    assert work.title == "Calculus"
    assert work.languages == ["en"]  # normalized from "eng"
    assert work.license == "Attribution-NonCommercial-ShareAlike"
    assert work.description == "A calculus textbook."
    assert work.source_url == f"{BASE}/textbooks/calculus"
    assert work.popularity is None  # assigned after all books are processed
    assert work.extra["copyright_year"] == 2016
    assert work.extra["review_rating"] == "4"
    assert work.primary_metric == 7
    assert work.extra["review_score"] == 4.07


def test_fetch_keeps_only_authors_as_creators():
    metadata = _metadata_with({f"{BASE}/textbooks/10.json": _record_payload()})

    (work,) = metadata.fetch([_ref("10")])

    assert [c.name for c in work.creators] == ["Gilbert Strang"]
    assert work.creators[0].sort_name == "Strang"


def test_fetch_maps_formats_and_subjects():
    metadata = _metadata_with({f"{BASE}/textbooks/10.json": _record_payload()})

    (work,) = metadata.fetch([_ref("10")])

    assert [(f.name, f.url) for f in work.formats] == [
        ("PDF", "https://example.org/calculus.pdf"),
        ("Online", "https://example.org/calculus"),
    ]
    assert work.formats[0].media_type == "application/pdf"
    assert [(c.id, c.name, c.kind) for c in work.collections] == [
        ("5", "Mathematics", "subject")
    ]


def test_fetch_skips_malformed_format_and_subject_entries():
    record = {
        **RECORD,
        "formats": [{"url": "https://example.org/unknown"}, "not a format"],
        "subjects": [{"id": 1}, {"name": "No ID"}, "not a subject"],
    }
    metadata = _metadata_with({f"{BASE}/textbooks/10.json": _record_payload(record)})

    (work,) = metadata.fetch([_ref("10")])

    assert work.formats == []
    assert work.collections == []


def test_fetch_persists_metadata_cache_with_atomic_replacement(tmp_path, monkeypatch):
    replacements: list[tuple[Path, Path]] = []
    original_replace = Path.replace

    def replace(source: Path, target: Path) -> Path:
        replacements.append((source, target))
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", replace)
    metadata = _metadata_with(
        {f"{BASE}/textbooks/10.json": _record_payload()}, cache_dir=tmp_path
    )

    list(metadata.fetch([_ref("10")]))

    cache_path = tmp_path / "otl_metadata" / "10.json"
    assert replacements
    assert replacements[0][0] != cache_path
    assert replacements[0][1] == cache_path
    assert json.loads(cache_path.read_text(encoding="utf-8")) == RECORD


def test_fetch_skips_missing_books():
    response = requests.Response()
    response.status_code = 404
    not_found = requests.HTTPError(response=response)
    metadata = _metadata_with(
        {f"{BASE}/textbooks/10.json": _record_payload()},
        errors={f"{BASE}/textbooks/99999.json": not_found},
    )

    works = list(metadata.fetch([_ref("99999"), _ref("10")]))

    assert [work.id for work in works] == ["10"]
