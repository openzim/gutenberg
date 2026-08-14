"""Tests for the persistent OTL invalid-edition URL cache."""

from pathlib import Path

from gutenberg2zim.sources.opentextbooks.invalid_urls import InvalidEditionCache


def test_add_persists_url_with_atomic_replacement(tmp_path, monkeypatch):
    cache_path = tmp_path / "otl_invalid_edition_urls.json"
    replacements: list[tuple[Path, Path]] = []
    original_replace = Path.replace

    def replace(source: Path, target: Path) -> Path:
        replacements.append((source, target))
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", replace)
    cache = InvalidEditionCache(tmp_path)

    cache.add("https://example.org/unavailable.pdf")

    assert replacements
    source, target = replacements[0]
    assert source != cache_path
    assert target == cache_path
    assert InvalidEditionCache(tmp_path).contains("https://example.org/unavailable.pdf")
