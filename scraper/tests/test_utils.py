from gutenberg2zim.core.utils import (
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    fname_for,
    normalize,
)


def test_book_name_for_fs(mock_work):
    assert book_name_for_fs(mock_work) == "Travels in the Great Desert of Sahara"


def test_book_name_for_fs_sanitizes_slashes(mock_work):
    mock_work.title = "Foo / Bar"
    assert book_name_for_fs(mock_work) == "Foo - Bar"


def test_book_name_for_fs_truncates_long_titles(mock_work):
    mock_work.title = "x" * 300
    assert len(book_name_for_fs(mock_work)) == 230


def test_article_name_for(mock_work):
    assert article_name_for(mock_work) == "Travels in the Great Desert of Sahara.22094"


def test_article_name_for_cover(mock_work):
    assert (
        article_name_for(mock_work, cover=True)
        == "Travels in the Great Desert of Sahara_cover.22094"
    )


def test_archive_name_for(mock_work):
    assert (
        archive_name_for(mock_work, "epub")
        == "Travels in the Great Desert of Sahara.22094.epub"
    )


def test_fname_for(mock_work):
    assert fname_for(mock_work, "html") == "22094.html"


def test_normalize_none():
    assert normalize(None) is None


def test_normalize_combines_characters():
    # "é" as e + combining acute should normalize to single codepoint
    assert normalize("é") == "é"
