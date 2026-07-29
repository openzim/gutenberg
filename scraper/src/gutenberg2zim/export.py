import io
import urllib.parse
import warnings
import zipfile
from collections.abc import Iterable
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from jinja2 import Environment, PackageLoader, select_autoescape
from zimscraperlib.image.optimization import optimize_jpeg, optimize_png
from zimscraperlib.zim.indexing import IndexData

from gutenberg2zim.adapters import work_to_book
from gutenberg2zim.constants import logger
from gutenberg2zim.core.work_store import WorkStore
from gutenberg2zim.core.zim_assembler import ZimAssembler
from gutenberg2zim.download import download_book_cover
from gutenberg2zim.iso639 import language_name
from gutenberg2zim.models import Author, Book
from gutenberg2zim.schemas import (
    Author as AuthorSchema,
)
from gutenberg2zim.schemas import (
    AuthorDetail,
    AuthorPreview,
    Authors,
    BookFormat,
    BookPreview,
    Books,
    Config,
    LCCShelf,
    LCCShelfPreview,
    LCCShelves,
)
from gutenberg2zim.schemas import (
    Book as BookSchema,
)
from gutenberg2zim.sources.gutenberg.plugins import (
    ImageProcessor,
    transform_image_path,
    update_html_for_static,
)
from gutenberg2zim.utils import (
    UTF8,
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    fname_for,
    save_file,
)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


jinja_env = Environment(
    loader=PackageLoader("gutenberg2zim", "templates"),
    autoescape=select_autoescape(("html", "htm", "xml")),
)


def fa_for_format(book_format):
    return {
        "html": "",
        "info": "fa-info-circle",
        "epub": "fa-download",
        "pdf": "fa-file-pdf-o",
    }.get(book_format, "fa-file-o")


def zim_link_prefix(book_format):
    return "../{}/".format({"html": "A", "epub": "I", "pdf": "I"}.get(book_format))


def urlencode(url):
    return urllib.parse.quote(url)


def save_bs_output(soup, fpath, encoding=UTF8):
    save_file(str(soup), fpath, encoding)


jinja_env.filters["book_name_for_fs"] = book_name_for_fs
jinja_env.filters["zim_link_prefix"] = zim_link_prefix
jinja_env.filters["language_name"] = language_name
jinja_env.filters["fa_for_format"] = fa_for_format
jinja_env.filters["urlencode"] = urlencode
jinja_env.filters["article_name_for"] = lambda book, cover=False: article_name_for(
    book, cover=cover
)
jinja_env.filters["archive_name_for"] = archive_name_for


def export_book(
    book: Book,
    book_files: dict[str, bytes],
    formats: list[str],
    mirror_url: str,
    assembler: ZimAssembler,
    _zim_name: str,
    *,
    _title_search: bool,
    _add_lcc_shelves: bool,
):
    """Export book to ZIM using in-memory content"""
    handle_book_files(
        book=book,
        book_files=book_files,
        formats=formats,
        assembler=assembler,
    )

    # Handle cover image
    cover_path = f"covers/{book.book_id}_cover_image.webp"

    if book.html_cover_path:
        # HTML has a cover image - create alias instead of storing duplicate
        # Use alias (not redirect) since this is an image, not HTML with relative paths
        logger.debug(
            f"Using HTML cover for book #{book.book_id}: {book.html_cover_path}"
        )
        assembler.add_alias(
            path=cover_path,
            title="",
            target=book.html_cover_path,
        )
    else:
        # No HTML cover - download from mirror
        cover_image = download_book_cover(mirror_url, book)

        if cover_image:
            logger.debug(f"Using downloaded cover for book #{book.book_id}")
            cover_image = optimize_content(book, cover_path, cover_image)
            assembler.add_item_for(
                path=cover_path,
                content=cover_image,
                mimetype="image/webp",
                is_front=False,
            )


def handle_book_files(
    book: Book,
    book_files: dict[str, bytes],
    formats: list[str],
    assembler: ZimAssembler,
):
    """Handle book files from in-memory content and add to ZIM"""

    # Find the main HTML file
    main_html_filename = f"{book.book_id}.html"
    html_content = None

    if main_html_filename in book_files:
        html_content = book_files[main_html_filename].decode("utf-8", errors="replace")

    if html_content:
        article_name = article_name_for(book)
        try:
            new_html = update_html_for_static(
                book=book, html_content=html_content, formats=formats
            )
        except Exception:
            raise

        # Add the optimized HTML directly to ZIM
        assembler.add_item_for(
            path=article_name,
            content=str(new_html),
            mimetype="text/html",
            is_front=False,
            title=book.title,
            auto_index=True,
        )

    # Handle other formats (epub, pdf)
    other_filenames = []
    for other_format in [
        fmt
        for fmt in formats
        if fmt != "html" and fmt not in str(book.unsupported_formats).split(",")
    ]:
        book_filename = fname_for(book, other_format)
        if book_filename in book_files:
            other_filenames.append(book_filename)
            try:
                archive_name = archive_name_for(book, other_format)
                content = book_files[book_filename]
                if other_format == "epub":
                    content = optimize_epub_bytes(content, book)
                assembler.add_item_for(
                    path=archive_name,
                    content=content,
                    is_front=False,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling {other_format}: {e}")
                raise

    # Process all associated files (images, companion HTML files, etc)
    for filename, file_content in book_files.items():
        # Skip the main HTML file as it's already processed
        if filename == main_html_filename:
            continue

        # Skip files matching a specific format since they have already been processed
        if filename in other_filenames:
            continue

        if filename.endswith((".html", ".htm")):
            # Process companion HTML files
            try:
                html_str = file_content.decode("utf-8", errors="replace")
                new_html = update_html_for_static(
                    book=book, html_content=html_str, formats=formats
                )
                assembler.add_item_for(
                    path=filename,
                    content=str(new_html),
                    mimetype="text/html",
                    is_front=False,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling companion HTML: {e}")
        else:
            # Add other files (images, etc) directly
            try:
                optimized_file_content = optimize_content(book, filename, file_content)
                output_filename = ImageProcessor.get_output_filename(filename)

                # Check if this is the cover image by comparing with transformed href
                # Note: filename is already transformed (e.g., "1_cover.jpg")
                # by download.py so we transform book._cover_href the same way
                if book._cover_href:
                    # Transform cover href same way we transform image paths
                    expected_cover = transform_image_path(
                        book.book_id, book._cover_href
                    )
                    expected_cover = ImageProcessor.get_output_filename(expected_cover)

                    if output_filename == expected_cover:
                        book.html_cover_path = output_filename
                        logger.debug(
                            f"Detected HTML cover for book #{book.book_id}: "
                            f"{output_filename}"
                        )

                assembler.add_item_for(
                    path=output_filename,
                    content=optimized_file_content,
                    is_front=False,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling file {filename}: {e}")


def optimize_content(book: Book, filename: str, file_content: bytes) -> bytes:
    """Optimize file content, converting images to WebP when appropriate."""
    # Convert JPG, PNG to WEBP for optimal file size
    if ImageProcessor.should_convert_to_webp(filename):
        return ImageProcessor.optimize_image_content(file_content)

    # Keep WebP and GIF files as-is
    ext = ImageProcessor.get_extension(filename)
    if ext in ("webp", "gif"):
        if ext == "gif":
            logger.debug(
                f"GIF file {filename} found in book {book.book_id} not optimized"
            )
        return file_content

    # Do not optimize other file types
    return file_content


def _optimize_epub_jpeg(data: bytes) -> bytes:
    """Optimize JPEG image in-memory for EPUB, keeping original format."""
    dst = io.BytesIO()
    optimize_jpeg(src=io.BytesIO(data), dst=dst)
    return dst.getvalue()


def _optimize_epub_png(data: bytes) -> bytes:
    """Optimize PNG image in-memory for EPUB, keeping original format."""
    dst = io.BytesIO()
    optimize_png(src=io.BytesIO(data), dst=dst)
    return dst.getvalue()


def _process_epub_html(data: bytes, book: Book, *, is_xml: bool = False) -> bytes:
    """Process HTML file from EPUB: remove Gutenberg markers and process content."""
    html_str = data.decode("utf-8", errors="replace")
    soup = update_html_for_static(
        book=book, html_content=html_str, formats=[], epub=True, is_xml=is_xml
    )
    return str(soup).encode(UTF8)


def _process_epub_ncx(data: bytes, book: Book | None = None) -> bytes:
    """Process NCX navigation file: remove license section."""
    ncx_str = data.decode("utf-8", errors="replace")
    soup = BeautifulSoup(ncx_str, "lxml-xml")
    pattern = "*** START: FULL LICENSE ***"
    for tag in soup.find_all("text"):
        if pattern in tag.text:
            book_info = f"book {book.book_id}" if book else "unknown book"
            logger.info(f"Found license section in NCX for {book_info}")
            s = tag.parent.parent  # pyright: ignore[reportOptionalMemberAccess]
            # Collect siblings before decomposing (decompose breaks iteration)
            siblings_to_remove = list(
                s.next_siblings  # pyright: ignore[reportOptionalMemberAccess]
            )
            s.decompose()  # pyright: ignore[reportOptionalMemberAccess]
            for sibling in siblings_to_remove:
                if hasattr(sibling, "decompose"):  # Skip text nodes
                    sibling.decompose()
            break
    return str(soup).encode(UTF8)


def optimize_epub_bytes(epub_bytes: bytes, book: Book) -> bytes:
    """Optimize EPUB in-memory: process HTML/NCX and optimize images without FS."""
    src_buf = io.BytesIO(epub_bytes)
    dst_buf = io.BytesIO()
    original_size = len(epub_bytes)

    with (
        zipfile.ZipFile(src_buf, "r") as src_zf,
        zipfile.ZipFile(dst_buf, "w", zipfile.ZIP_DEFLATED) as dst_zf,
    ):
        infos = src_zf.infolist()
        mimetype_info = next(
            (info for info in infos if info.filename == "mimetype"), None
        )
        if mimetype_info is None:
            raise ValueError("EPUB is missing its mimetype entry")

        # Write mimetype first, uncompressed, per EPUB spec
        dst_zf.writestr(
            "mimetype",
            src_zf.read(mimetype_info),
            compress_type=zipfile.ZIP_STORED,
        )

        for info in infos:
            if info.filename == "mimetype":
                continue

            name = info.filename
            data = src_zf.read(name)
            suffix = Path(name).suffix.lower()

            if suffix in (".jpg", ".jpeg"):
                optimized_data = _optimize_epub_jpeg(data)
                if len(optimized_data) < len(data):  # ignore bigger compressed version
                    data = optimized_data
            elif suffix == ".png":
                optimized_data = _optimize_epub_png(data)
                if len(optimized_data) < len(data):  # ignore bigger compressed version
                    data = optimized_data
            elif suffix in (".gif", ".webp"):
                logger.warning(
                    f"Unexpected {suffix} image in EPUB for book {book.book_id}: {name}"
                )
            elif suffix in (".htm", ".html", ".xhtml"):
                data = _process_epub_html(data, book, is_xml=(suffix == ".xhtml"))
            elif suffix == ".ncx":
                data = _process_epub_ncx(data, book)

            dst_zf.writestr(info, data)

    optimized_bytes = dst_buf.getvalue()
    optimized_size = len(optimized_bytes)
    if optimized_size > original_size:
        logger.warning(
            f"Optimized EPUB for book {book.book_id} is larger than original: "
            f"{optimized_size} > {original_size} bytes"
        )
    else:
        logger.debug(
            f"Optimized EPUB for book {book.book_id}: "
            f"{optimized_size} < {original_size} bytes"
        )

    return optimized_bytes


def _all_books(work_store: WorkStore) -> list[Book]:
    """Get all works from the store, converted back to legacy Book objects"""
    return [work_to_book(work) for work in work_store.works]


def _lcc_shelf_list_for_books(books: Iterable[Book]):
    return sorted({book.lcc_shelf for book in books if book.lcc_shelf})


def lcc_shelf_list(work_store: WorkStore):
    return _lcc_shelf_list_for_books(_all_books(work_store))


def lcc_shelf_list_language(lang, work_store: WorkStore):
    return _lcc_shelf_list_for_books(
        filter(lambda book: lang in book.languages, _all_books(work_store))
    )


def _build_author_books_map(books: Iterable[Book]) -> dict[str, list[Book]]:
    """Build a mapping from author gut_id to their books."""
    author_books_map: dict[str, list[Book]] = {}
    for book in books:
        author_id = book.author.gut_id
        if author_id not in author_books_map:
            author_books_map[author_id] = []
        author_books_map[author_id].append(book)
    return author_books_map


# JSON Generation Functions for Vue.js UI


def _get_authors_with_books(work_store: WorkStore) -> list[Author]:
    """Get only authors who have at least one book in the work store"""
    all_books = _all_books(work_store)
    authors_dict = {book.author.gut_id: book.author for book in all_books}
    return list(authors_dict.values())


def _author_to_preview(
    author: Author, author_stats: dict[str, tuple[int, int]]
) -> AuthorPreview:
    """Convert Author dataclass to AuthorPreview schema"""
    book_count, total_popularity = author_stats.get(author.gut_id, (0, 0))
    return AuthorPreview(
        id=author.gut_id,
        name=author.name(),
        book_count=book_count,
        total_popularity=total_popularity,
    )


def _author_to_schema(author: Author) -> AuthorSchema:
    """Convert Author dataclass to Author schema"""
    return AuthorSchema(
        id=author.gut_id,
        first_name=author.first_names,
        last_name=author.last_name,
        birth_year=author.birth_year,
        death_year=author.death_year,
        name=author.name(),
    )


def _book_to_preview(
    book: Book, formats: list[str], author_stats: dict[str, tuple[int, int]]
) -> BookPreview:
    """Convert Book dataclass to BookPreview schema"""
    cover_path = f"covers/{book.book_id}_cover_image.webp" if book.has_cover else None

    return BookPreview(
        id=book.book_id,
        title=book.title,
        author=_author_to_preview(book.author, author_stats),
        languages=book.languages,
        popularity=book.popularity,
        cover_path=cover_path,
        lcc_shelf=book.lcc_shelf,
        available_formats=book.requested_formats(formats),
        description=book.description,
    )


def _book_to_schema(book: Book, formats: list[str]) -> BookSchema:
    """Convert Book dataclass to Book schema with formats"""
    cover_path = f"covers/{book.book_id}_cover_image.webp" if book.has_cover else None

    book_formats: list[BookFormat] = []
    available_formats = book.requested_formats(formats)

    for fmt in formats:
        if fmt in available_formats:
            if fmt == "html":
                path = article_name_for(book)
            else:
                path = archive_name_for(book, fmt)
            book_formats.append(
                BookFormat(
                    format=fmt,
                    path=path,
                    available=True,
                )
            )
        else:
            book_formats.append(
                BookFormat(
                    format=fmt,
                    path="",
                    available=False,
                )
            )

    return BookSchema(
        id=book.book_id,
        title=book.title,
        subtitle=book.subtitle,
        author=_author_to_schema(book.author),
        languages=book.languages,
        license=book.license,
        downloads=book.downloads,
        popularity=book.popularity,
        lcc_shelf=book.lcc_shelf,
        cover_path=cover_path,
        formats=book_formats,
        description=book.description,
    )


def _lcc_shelf_to_preview(shelf_code: str, all_books: list[Book]) -> LCCShelfPreview:
    """Convert LCC shelf code to LCCShelfPreview schema"""
    shelf_books = [book for book in all_books if book.lcc_shelf == shelf_code]
    book_count = len(shelf_books)
    total_popularity = sum(book.popularity for book in shelf_books)
    return LCCShelfPreview(
        code=shelf_code,
        name=None,
        book_count=book_count,
        total_popularity=total_popularity,
    )


def add_index_entry(
    title: str, content: str, fname: str, vue_route: str, assembler: ZimAssembler
) -> None:
    """Add a custom item to the ZIM index with HTML redirect to Vue.js route.

    Args:
        title: Title for the index entry
        content: Content/description for search indexing
        fname: Filename for the index entry (e.g., "book_12345")
        vue_route: Vue.js route path (e.g., "book/12345")
        assembler: The ZIM assembler to add the item to
    """
    redirect_url = f"../index.html#/{vue_route}"
    safe_title = escape(title)
    safe_content = escape(content)
    safe_redirect_url = escape(redirect_url, quote=True)
    html_content = (
        f"<html><head><title>{safe_title}</title>"
        f'<meta http-equiv="refresh" content="0;URL=\'{safe_redirect_url}\'" />'
        f"</head><body>{safe_content}</body></html>"
    )

    logger.debug(f"Adding {fname} to ZIM index")
    assembler.add_item_for(
        title=title,
        path=f"index/{fname}",
        content=html_content,
        mimetype="text/html",
        index_data=IndexData(title=title, content=content),
    )


def generate_json_files(
    zim_name: str,
    formats: list[str],
    work_store: WorkStore,
    assembler: ZimAssembler,
    title: str | None = None,
    description: str | None = None,
    *,
    add_lcc_shelves: bool = False,
    primary_color: str | None = None,
    secondary_color: str | None = None,
) -> None:
    """Generate all JSON files for Vue.js frontend"""
    logger.info("Generating JSON files for Vue.js UI")

    # Maximum number of books to include in index entries
    max_books_in_index = 10

    # Fetch data once and reuse
    all_books = _all_books(work_store)
    all_authors = _get_authors_with_books(work_store)

    # Build author stats once for O(1) lookups
    author_stats: dict[str, tuple[int, int]] = {}
    for book in all_books:
        gut_id = book.author.gut_id
        count, pop = author_stats.get(gut_id, (0, 0))
        author_stats[gut_id] = (count + 1, pop + book.popularity)

    logger.info("Generating high-level JSON files")
    logger.debug("Generating books.json")
    books_preview = [
        _book_to_preview(book, formats, author_stats) for book in all_books
    ]
    books_collection = Books(books=books_preview, total_count=len(books_preview))
    assembler.add_item_for(
        path="books.json",
        content=books_collection.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    logger.debug("Generating authors.json")
    authors_preview = [
        _author_to_preview(author, author_stats) for author in all_authors
    ]
    authors_collection = Authors(
        authors=authors_preview, total_count=len(authors_preview)
    )
    assembler.add_item_for(
        path="authors.json",
        content=authors_collection.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    if add_lcc_shelves:
        logger.debug("Generating lcc_shelves.json")
        shelves_preview = [
            _lcc_shelf_to_preview(shelf_code, all_books)
            for shelf_code in _lcc_shelf_list_for_books(all_books)
        ]
        shelves_collection = LCCShelves(
            shelves=shelves_preview, total_count=len(shelves_preview)
        )
        assembler.add_item_for(
            path="lcc_shelves.json",
            content=shelves_collection.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

    logger.debug("Generating config.json")
    config = Config(
        title=title or zim_name or "Project Gutenberg Library",
        description=description,
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
    assembler.add_item_for(
        path="config.json",
        content=config.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    logger.info("Generating detail JSON files")
    logger.debug("Generating book detail files and index entries")
    for book in all_books:
        book_detail = _book_to_schema(book, formats)
        assembler.add_item_for(
            path=f"books/{book.book_id}.json",
            content=book_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

        # Add index entry for book
        book_description = book_detail.description or f"Book by {book.author.name()}"
        # Build searchable content with key metadata
        index_parts = [book_description, f"by {book.author.name()}"]

        if book.subtitle:
            index_parts.insert(0, book.subtitle)
        if book.languages:
            index_parts.append(f"Languages: {', '.join(book.languages)}")
        if book.lcc_shelf:
            index_parts.append(f"LCC Shelf: {book.lcc_shelf}")

        add_index_entry(
            title=book.title,
            content=". ".join(index_parts) + ".",
            fname=f"book_{book.book_id}",
            vue_route=f"book/{book.book_id}",
            assembler=assembler,
        )

    logger.debug("Generating author detail files and index entries")
    # Build author_id -> books mapping once to avoid O(authors * books) scans
    author_books_map = _build_author_books_map(all_books)

    for author in all_authors:
        author_books = [
            _book_to_preview(book, formats, author_stats)
            for book in author_books_map.get(author.gut_id, [])
        ]
        author_detail = AuthorDetail(
            id=author.gut_id,
            first_name=author.first_names,
            last_name=author.last_name,
            birth_year=author.birth_year,
            death_year=author.death_year,
            name=author.name(),
            books=author_books,
            book_count=len(author_books),
        )

        assembler.add_item_for(
            path=f"authors/{author.gut_id}.json",
            content=author_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

        # Add index entry for author
        author_parts = [f"Author: {author.name()}"]

        if author.birth_year or author.death_year:
            years = f"{author.birth_year or ''} - {author.death_year or ''}".strip(" -")
            author_parts.append(f"({years})")

        author_parts.append(f"{len(author_books)} book(s)")

        # Add book titles for searchability
        if author_books:
            titles = [book.title for book in author_books[:max_books_in_index]]
            author_parts.append("Books: " + ", ".join(titles))
            if len(author_books) > max_books_in_index:
                author_parts.append(
                    f"and {len(author_books) - max_books_in_index} more"
                )

        add_index_entry(
            title=author.name(),
            content=". ".join(author_parts) + ".",
            fname=f"author_{author.gut_id}",
            vue_route=f"author/{author.gut_id}",
            assembler=assembler,
        )

    if add_lcc_shelves:
        logger.debug("Generating LCC shelf detail files and index entries")
        for shelf_code in _lcc_shelf_list_for_books(all_books):
            shelf_books = [
                _book_to_preview(book, formats, author_stats)
                for book in all_books
                if book.lcc_shelf == shelf_code
            ]
            shelf_detail = LCCShelf(
                code=shelf_code,
                name=None,
                books=shelf_books,
                book_count=len(shelf_books),
            )
            assembler.add_item_for(
                path=f"lcc_shelves/{shelf_code}.json",
                content=shelf_detail.model_dump_json(by_alias=True, indent=2),
                mimetype="application/json",
                is_front=False,
            )

            shelf_title = f"LCC Shelf {shelf_code}"
            shelf_parts = [
                f"Library of Congress Classification shelf {shelf_code}",
                f"{len(shelf_books)} book(s)",
            ]

            # Add book titles and authors for searchability
            if shelf_books:
                book_entries = [
                    f"{book.title} by {book.author.name}"
                    for book in shelf_books[:max_books_in_index]
                ]
                shelf_parts.append("Books: " + ", ".join(book_entries))
                if len(shelf_books) > max_books_in_index:
                    shelf_parts.append(
                        f"and {len(shelf_books) - max_books_in_index} more"
                    )

            add_index_entry(
                title=shelf_title,
                content=". ".join(shelf_parts) + ".",
                fname=f"lcc_shelf_{shelf_code}",
                vue_route=f"lcc-shelf/{shelf_code}",
                assembler=assembler,
            )

    # Add index entries for main listing pages
    add_index_entry(
        title="All Books - Project Gutenberg",
        content=f"Browse all {len(all_books)} books available in Project Gutenberg. "
        f"Search and filter by language, format, author, and more.",
        fname="books_list",
        vue_route="books",
        assembler=assembler,
    )

    add_index_entry(
        title="All Authors - Project Gutenberg",
        content=f"Browse all {len(all_authors)} authors in Project Gutenberg. "
        f"Discover books by your favorite authors.",
        fname="authors_list",
        vue_route="authors",
        assembler=assembler,
    )

    if add_lcc_shelves:
        shelves = _lcc_shelf_list_for_books(all_books)
        add_index_entry(
            title="LCC Shelves - Project Gutenberg",
            content=f"Browse books by Library of Congress Classification. "
            f"{len(shelves)} shelves available covering various subjects and topics.",
            fname="lcc_shelves_list",
            vue_route="lcc-shelves",
            assembler=assembler,
        )

    logger.info("JSON file generation completed")


def export_infobox_assets(assembler: ZimAssembler) -> None:
    """Export infobox CSS, JS, and icon files to ZIM"""
    templates_dir = Path(__file__).parent / "templates"

    assets = [
        ("css/gutenberg-infobox.css", "css", "text/css"),
        ("js/gutenberg-infobox.js", "js", "text/javascript"),
        ("icons/info.svg", "icons", "image/svg+xml"),
        ("icons/epub.svg", "icons", "image/svg+xml"),
        ("icons/pdf.svg", "icons", "image/svg+xml"),
        ("icons/scroll-up.svg", "icons", "image/svg+xml"),
    ]

    for zim_path, subdir, mimetype in assets:
        file_path = templates_dir / subdir / Path(zim_path).name
        if not file_path.exists():
            logger.warning(f"Infobox asset not found: {file_path}")
            continue
        logger.debug(f"Adding {zim_path} to ZIM")
        assembler.add_item_for(
            path=zim_path,
            fpath=file_path,
            mimetype=mimetype,
            is_front=False,
        )


def generate_noscript_pages(
    formats: list[str],
    work_store: WorkStore,
    assembler: ZimAssembler,
) -> None:
    """Generate No-JavaScript fallback HTML pages"""
    logger.info("Generating No-JS fallback pages")

    # Add common CSS file to ZIM
    common_css_path = Path(__file__).parent / "templates" / "noscript" / "common.css"
    if common_css_path.exists():
        logger.debug("Adding noscript/common.css to ZIM")
        assembler.add_item_for(
            path="noscript/common.css",
            fpath=common_css_path,
            mimetype="text/css",
            is_front=False,
        )
    all_books = _all_books(work_store)
    all_authors = _get_authors_with_books(work_store)
    shelves = _lcc_shelf_list_for_books(all_books)
    shelf_books_map: dict[str, list[Book]] = {
        shelf_code: [book for book in all_books if book.lcc_shelf == shelf_code]
        for shelf_code in shelves
    }

    # Generate books listing page
    logger.debug("Generating noscript/books.html")
    books_template = jinja_env.get_template("noscript/books.html")
    books_html = books_template.render(
        books=all_books,
        formats=formats,
    )
    assembler.add_item_for(
        path="noscript/books.html",
        content=books_html,
        mimetype="text/html",
        is_front=False,
        title="All Books - Project Gutenberg",
        auto_index=False,
    )

    # Generate authors listing page
    logger.debug("Generating noscript/authors.html")
    # Reuse author_books_map for book counts
    author_books_map = _build_author_books_map(all_books)
    author_book_counts = {
        author_id: len(books) for author_id, books in author_books_map.items()
    }
    authors_template = jinja_env.get_template("noscript/authors.html")
    authors_html = authors_template.render(
        authors=all_authors,
        all_books=all_books,
        author_book_counts=author_book_counts,
    )
    assembler.add_item_for(
        path="noscript/authors.html",
        content=authors_html,
        mimetype="text/html",
        is_front=False,
        title="All Authors - Project Gutenberg",
        auto_index=False,
    )

    logger.debug("Generating noscript/lcc_shelves.html")
    shelves_template = jinja_env.get_template("noscript/lcc_shelves.html")
    shelves_html = shelves_template.render(
        shelves=[
            {
                "code": code,
                "book_count": len(shelf_books_map.get(code, [])),
            }
            for code in shelves
        ]
    )
    assembler.add_item_for(
        path="noscript/lcc_shelves.html",
        content=shelves_html,
        mimetype="text/html",
        is_front=False,
        title="LCC Shelves - Project Gutenberg",
        auto_index=False,
    )

    logger.debug("Generating No-JS LCC shelf detail pages")
    shelf_template = jinja_env.get_template("noscript/lcc_shelf.html")
    for shelf_code in shelves:
        shelf_books = shelf_books_map.get(shelf_code, [])
        shelf_html = shelf_template.render(
            shelf_code=shelf_code,
            books=shelf_books,
            formats=formats,
        )
        assembler.add_item_for(
            path=f"noscript/lcc_shelf_{shelf_code}.html",
            content=shelf_html,
            mimetype="text/html",
            is_front=False,
            title=f"LCC Shelf {shelf_code}",
            auto_index=False,
        )

    # Generate individual book pages
    logger.debug("Generating No-JS book detail pages")
    book_template = jinja_env.get_template("noscript/book.html")
    for book in all_books:
        book_html = book_template.render(
            book=book,
            formats=formats,
        )
        assembler.add_item_for(
            path=f"noscript/book_{book.book_id}.html",
            content=book_html,
            mimetype="text/html",
            is_front=False,
            title=book.title,
            auto_index=False,
        )

    # Generate individual author pages
    logger.debug("Generating No-JS author pages")
    author_template = jinja_env.get_template("noscript/author.html")
    for author in all_authors:
        author_books = author_books_map.get(author.gut_id, [])
        author_html = author_template.render(
            author=author,
            author_books=author_books,
        )
        assembler.add_item_for(
            path=f"noscript/author_{author.gut_id}.html",
            content=author_html,
            mimetype="text/html",
            is_front=False,
            title=author.name(),
            auto_index=False,
        )

    logger.info("No-JS fallback pages generation completed")
