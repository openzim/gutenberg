import pytest

from gutenberg2zim.core.language import get_zim_language_metadata, resolve_language
from gutenberg2zim.sources.gutenberg.catalog import CatalogEntry


def _make_books(languages_per_book: list[list[str]]) -> list[CatalogEntry]:
    return [
        CatalogEntry(book_id=i, languages=langs, lcc_shelf="")
        for i, langs in enumerate(languages_per_book)
    ]


# resolve_language
def test_resolve_language_two_letter_code():
    assert resolve_language("en") == ["eng"]


def test_resolve_language_three_letter_code():
    assert resolve_language("gla") == ["gla"]


def test_resolve_language_zim_map_override():
    assert resolve_language("nah") == ["nhe"]


def test_resolve_language_explicitly_empty():
    assert resolve_language("myn") == []


def test_resolve_language_unknown_code():
    assert resolve_language("zzz") == []


# get_zim_language_metadata
def test_two_letter_codes_resolve():
    books = _make_books([["en"], ["en"], ["fr"]])
    result = get_zim_language_metadata(["en", "fr"], books)
    assert "eng" in result
    assert "fra" in result


def test_sorted_by_book_count_descending():
    books = _make_books([["fr"], ["fr"], ["fr"], ["en"]])
    result = get_zim_language_metadata(["en", "fr"], books)
    assert result == ["fra", "eng"]


def test_unresolved_code_raises():
    books = _make_books([["myn"]])
    with pytest.raises(ValueError, match="myn"):
        get_zim_language_metadata(["myn"], books)


def test_empty_languages_returns_empty():
    books = _make_books([["en"]])
    result = get_zim_language_metadata([], books)
    assert result == []


def test_counts_accumulate_when_codes_collapse_to_same_zim_language():
    # "en" and "eng" both resolve to "eng"; counts must add, not overwrite
    books = _make_books([["en"], ["en"], ["eng"], ["fr"]])
    result = get_zim_language_metadata(["en", "eng", "fr"], books)
    assert result == ["eng", "fra"]


# Regression tests for #337
def test_gla_resolves():
    books = _make_books([["gla"]])
    assert get_zim_language_metadata(["gla"], books) == ["gla"]


def test_nap_resolves():
    books = _make_books([["nap"]])
    assert get_zim_language_metadata(["nap"], books) == ["nap"]


def test_oji_resolves():
    books = _make_books([["oji"]])
    assert get_zim_language_metadata(["oji"], books) == ["oji"]
