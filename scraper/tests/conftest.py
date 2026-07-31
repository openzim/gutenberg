from unittest.mock import MagicMock

import pytest

from gutenberg2zim.sources.gutenberg.models import Author, Book


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary output folder for ZIMs and downloads"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_author():
    return Author(
        gut_id="3485",
        last_name="Richardson",
        first_names="James",
        birth_year="1806",
        death_year="1851",
    )


@pytest.fixture
def mock_book(mock_author):
    return Book(
        book_id=22094,
        title="Travels in the Great Desert of Sahara",
        author=mock_author,
        languages=["en"],
        license="Public domain in the USA.",
        downloads=548,
        lcc_shelf="DT",
        has_cover=True,
    )


@pytest.fixture
def mock_zim_creator():
    return MagicMock(name="zim_creator")
