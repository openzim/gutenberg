from unittest.mock import MagicMock

import pytest

from gutenberg2zim.core.models import CollectionRef, Cover, Creator, Work


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary output folder for ZIMs and downloads"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_creator():
    return Creator(
        id="3485",
        name="James Richardson",
        sort_name="Richardson",
        birth_date=1806,
        death_date=1851,
        extra={
            "first_names": "James",
            "birth_year_raw": "1806",
            "death_year_raw": "1851",
        },
    )


@pytest.fixture
def mock_work(mock_creator):
    return Work(
        id="22094",
        source="gutenberg",
        title="Travels in the Great Desert of Sahara",
        creators=[mock_creator],
        languages=["en"],
        license="Public domain in the USA.",
        cover=Cover(),
        collections=[CollectionRef(id="DT", name="DT", kind="lcc_shelf")],
        extra={"downloads": 548, "has_cover": True},
    )


@pytest.fixture
def mock_zim_creator():
    return MagicMock(name="zim_creator")
