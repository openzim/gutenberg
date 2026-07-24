from gutenberg2zim.utils import (
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    fname_for,
    normalize,
)


def test_book_name_for_fs(mock_book):
    assert book_name_for_fs(mock_book) == "Travels in the Great Desert of Sahara"


def test_book_name_for_fs_sanitizes_slashes(mock_book):
    mock_book.title = "Foo / Bar"
    assert book_name_for_fs(mock_book) == "Foo - Bar"


def test_book_name_for_fs_truncates_long_titles(mock_book):
    mock_book.title = "x" * 300
    assert len(book_name_for_fs(mock_book)) == 230


def test_article_name_for(mock_book):
    assert article_name_for(mock_book) == "Travels in the Great Desert of Sahara.22094"


def test_article_name_for_cover(mock_book):
    assert (
        article_name_for(mock_book, cover=True)
        == "Travels in the Great Desert of Sahara_cover.22094"
    )


def test_archive_name_for(mock_book):
    assert (
        archive_name_for(mock_book, "epub")
        == "Travels in the Great Desert of Sahara.22094.epub"
    )


def test_fname_for(mock_book):
    assert fname_for(mock_book, "html") == "22094.html"


def test_normalize_none():
    assert normalize(None) is None


def test_normalize_combines_characters():
    # "é" as e + combining acute should normalize to single codepoint
    assert normalize("é") == "é"
