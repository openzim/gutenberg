from unittest.mock import MagicMock, patch

import pytest

from gutenberg2zim.models import Author, Book, repository


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
def mock_repository():
    """Provide a clean singleton repository and restore it after the test"""
    repository.reset()
    yield repository
    repository.reset()


@pytest.fixture
def mock_zim_creator():
    return MagicMock(name="zim_creator")


@pytest.fixture
def mock_requests():
    """Mock gutenberg2zim.download.requests for HTTP-less tests"""
    with patch("gutenberg2zim.download.requests") as mocked:
        yield mocked
