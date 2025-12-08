import urllib.parse
from collections.abc import Iterable
from pathlib import Path

import bs4
from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, PackageLoader
from zimscraperlib.zim.indexing import IndexData

from gutenberg2zim.constants import logger
from gutenberg2zim.iso639 import language_name
from gutenberg2zim.models import Author, Book, repository
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
from gutenberg2zim.shared import Global
from gutenberg2zim.utils import (
    UTF8,
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    fname_for,
    read_file,
    save_file,
)

jinja_env = Environment(  # noqa: S701
    loader=PackageLoader("gutenberg2zim", "templates")
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
jinja_env.filters["archive_name_for"] = lambda book, fmt: archive_name_for(book, fmt)


def html_content_for(book: Book, src_dir):
    html_fpath = src_dir / fname_for(book, "html")

    # is HTML file present?
    if not html_fpath.exists():
        logger.warn(f"Missing HTML content for #{book.book_id} at {html_fpath}")
        return None, None

    try:
        return read_file(html_fpath)
    except UnicodeDecodeError:
        logger.error(f"Unable to read HTML content: {html_fpath}")
        raise


def update_html_for_static(book, html_content, formats, *, epub=False):
    soup = BeautifulSoup(html_content, "lxml")

    # remove encoding as we're saving to UTF8 anyway
    encoding_specified = False
    for meta in soup.find_all("meta"):
        if "charset" in meta.attrs:
            encoding_specified = True
            # logger.debug("found <meta> tag with charset `{}`"
            #              .format(meta.attrs.get('charset')))
            del meta.attrs["charset"]
        elif "content" in meta.attrs and "charset=" in meta.get_attribute_list(
            "content"
        ):
            try:
                ctype, _ = meta.get_attribute_list("content")[0].split(";", 1)
            except Exception:  # noqa: S112
                continue
            else:
                encoding_specified = True
            # logger.debug("found <meta> tag with content;charset `{}`"
            #              .format(meta.attrs.get('content')))
            meta.attrs["content"] = ctype
    if encoding_specified:
        # logger.debug("charset was found and removed")
        pass

    # update all <img> links from images/xxx.xxx to {id}_xxx.xxx
    if not epub:
        for img in soup.find_all("img"):
            if "src" in img.attrs:
                img.attrs["src"] = img.get_attribute_list("src")[0].replace(
                    "images/", f"{book.book_id}_"
                )

    # update all <a> links to internal HTML pages
    # should only apply to relative URLs to HTML files.
    # examples on #16816, #22889, #30021
    def replacablement_link(book, url):
        try:
            urlp, anchor = url.rsplit("#", 1)
        except ValueError:
            urlp = url
            anchor = None
        if "/" in urlp:
            return None

        if len(urlp.strip()):
            nurl = f"{book.book_id}_{urlp}"
        else:
            nurl = ""

        if anchor is not None:
            return "#".join([nurl, anchor])

        return nurl

    if not epub:
        for link in soup.find_all("a"):
            new_link = replacablement_link(book=book, url=link.attrs.get("href", ""))
            if new_link is not None:
                link.attrs["href"] = new_link

    # Add the title
    if not epub:
        if soup.title:
            soup.title.string = book.title
        else:
            if not soup.html:
                raise Exception("HTML should be set")
            head = soup.find("head")
            if not head:
                head = soup.new_tag("head")
                soup.html.insert(0, head)
            title_tag = soup.new_tag("title")
            title_tag.string = book.title
            head.append(title_tag)

    patterns = [
        (
            "*** START OF THE PROJECT GUTENBERG EBOOK",
            "*** END OF THE PROJECT GUTENBERG EBOOK",
        ),
        (
            "***START OF THE PROJECT GUTENBERG EBOOK",
            "***END OF THE PROJECT GUTENBERG EBOOK",
        ),
        (
            "<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>",
            "<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>",
        ),
        # ePub only
        ("*** START OF THIS PROJECT GUTENBERG EBOOK", "*** START: FULL LICENSE ***"),
        (
            "*END THE SMALL PRINT! FOR PUBLIC DOMAIN ETEXT",
            "——————————————————————————-",
        ),
        (
            "*** START OF THIS PROJECT GUTENBERG EBOOK",
            "*** END OF THIS PROJECT GUTENBERG EBOOK",
        ),
        ("***START OF THE PROJECT GUTENBERG", "***END OF THE PROJECT GUTENBERG EBOOK"),
        (
            "COPYRIGHT PROTECTED ETEXTS*END*",
            "===========================================================",
        ),
        (
            "Nous remercions la Bibliothèque Nationale de France qui a mis à",
            "The Project Gutenberg Etext of",
        ),
        (
            "Nous remercions la Bibliothèque Nationale de France qui a mis à",
            "End of The Project Gutenberg EBook",
        ),
        (
            "=========================================================="
            "===============",
            "——————————————————————————-",
        ),
        ("Project Gutenberg Etext", "End of Project Gutenberg Etext"),
        ("Text encoding is iso-8859-1", "Fin de Project Gutenberg Etext"),
        ("—————————————————-", "Encode an ISO 8859/1 Etext into LaTeX or HTML"),
    ]

    body = soup.find("body")
    if not isinstance(body, Tag):
        return
    try:
        is_encapsulated_in_div = (
            sum(
                [
                    1
                    for e in body.children
                    if not isinstance(e, bs4.element.NavigableString)
                ]
            )
            == 1
        )
    except Exception:
        is_encapsulated_in_div = False

    if not is_encapsulated_in_div:
        for start_of_text, end_of_text in patterns:
            if start_of_text not in body.text and end_of_text not in body.text:
                continue

            if start_of_text in body.text and end_of_text in body.text:
                remove = True
                for child in body.children:
                    if not isinstance(child, bs4.Tag):
                        continue
                    if end_of_text in getattr(child, "text", ""):
                        remove = True
                    if start_of_text in getattr(child, "text", ""):
                        child.decompose()
                        remove = False
                    if remove:
                        child.decompose()
                break

            elif start_of_text in body.text:
                remove = True
                for child in body.children:
                    if not isinstance(child, bs4.Tag):
                        raise Exception("start_of_text child should be a Tag class")
                    if start_of_text in getattr(child, "text", ""):
                        child.decompose()
                        remove = False
                    if remove:
                        child.decompose()
                break
            elif end_of_text in body.text:
                remove = False
                for child in body.children:
                    if not isinstance(child, bs4.Tag):
                        raise Exception("end_of_text child should be a Tag class")
                    if end_of_text in getattr(child, "text", ""):
                        remove = True
                    if remove:
                        child.decompose()
                break

    # build infobox
    if not epub:
        infobox = jinja_env.get_template("book_infobox.html")
        infobox_html = infobox.render({"book": book, "formats": formats})
        info_soup = BeautifulSoup(infobox_html, "lxml")
        info_box = info_soup.find("div")
        if not isinstance(info_box, Tag):
            raise Exception("info_box div should be a Tag class")
        body.insert(0, info_box)
        
        # Ensure head exists
        head = soup.find("head")
        if not head:
            html = soup.find("html")
            if not isinstance(html, Tag):
                raise Exception("html should be a Tag class")
            head = soup.new_tag("head")
            html.insert(0, head)
        
        # Add CSS link if not already present
        if not soup.find("link", {"href": "css/gutenberg-infobox.css"}):
            css_link = soup.new_tag("link", rel="stylesheet", href="css/gutenberg-infobox.css", type="text/css")
            head.append(css_link)
        
        # Add JS script at the end of body (runs after DOM is ready)
        if not soup.find("script", {"src": "js/gutenberg-infobox.js"}):
            js_script = soup.new_tag("script", src="js/gutenberg-infobox.js", type="text/javascript")
            body.append(js_script)

    # if there is no charset, set it to utf8
    if not epub:
        meta = BeautifulSoup(
            '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />',
            "lxml",
        )
        head = soup.find("head")
        html = soup.find("html")
        if not isinstance(head, Tag):
            raise Exception("head should be a Tag class")
        if not isinstance(html, Tag):
            raise Exception("html should be a Tag class")
        if not isinstance(meta.head, Tag):
            raise Exception("meta.head should be a Tag class")
        if head:
            head.insert(0, meta.head.contents[0])
        elif html:
            html.insert(0, meta.head)
        else:
            soup.insert(0, meta.head)

        return html

    return soup


def export_book(
    book: Book,
    book_files: dict[str, bytes],
    cover_image: bytes | None,
    formats: list[str],
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
    )

    if cover_image:
        cover_path = f"covers/{book.book_id}_cover_image.jpg"
        Global.add_item_for(
            path=cover_path,
            content=cover_image,
            mimetype="image/jpeg",
            is_front=False,
        )


def handle_book_files(
    book: Book,
    book_files: dict[str, bytes],
    formats: list[str],
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
        Global.add_item_for(
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
                Global.add_item_for(
                    path=archive_name,
                    content=book_files[book_filename],
                    is_front=False,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling {other_format}: {e}")

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
                Global.add_item_for(
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
                Global.add_item_for(
                    path=filename,
                    content=file_content,
                    is_front=False,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling file {filename}: {e}")


def _lcc_shelf_list_for_books(books: Iterable[Book]):
    return sorted({book.lcc_shelf for book in books if book.lcc_shelf})


def lcc_shelf_list():
    return _lcc_shelf_list_for_books(repository.get_all_books())


def lcc_shelf_list_language(lang):
    return _lcc_shelf_list_for_books(
        filter(lambda book: lang in book.languages, repository.get_all_books())
    )


# JSON Generation Functions for Vue.js UI


def _author_to_preview(author: Author) -> AuthorPreview:
    """Convert Author dataclass to AuthorPreview schema"""
    book_count = sum(
        1 for book in repository.get_all_books() if book.author.gut_id == author.gut_id
    )
    return AuthorPreview(
        id=author.gut_id,
        name=author.name(),
        book_count=book_count,
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


def _book_to_preview(book: Book) -> BookPreview:
    """Convert Book dataclass to BookPreview schema"""
    cover_path = f"covers/{book.book_id}_cover_image.jpg" if book.cover_page else None

    return BookPreview(
        id=book.book_id,
        title=book.title,
        author=_author_to_preview(book.author),
        languages=book.languages,
        popularity=book.popularity,
        cover_path=cover_path,
        lcc_shelf=book.lcc_shelf,
    )


def _book_to_schema(book: Book, formats: list[str]) -> BookSchema:
    """Convert Book dataclass to Book schema with formats"""
    cover_path = f"covers/{book.book_id}_cover_image.jpg" if book.cover_page else None

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
        description=None,
    )


def _lcc_shelf_to_preview(shelf_code: str) -> LCCShelfPreview:
    """Convert LCC shelf code to LCCShelfPreview schema"""
    book_count = sum(
        1 for book in repository.get_all_books() if book.lcc_shelf == shelf_code
    )
    return LCCShelfPreview(
        code=shelf_code,
        name=None,
        book_count=book_count,
    )


def add_index_entry(title: str, content: str, fname: str, vue_route: str) -> None:
    """Add a custom item to the ZIM index with HTML redirect to Vue.js route.

    Args:
        title: Title for the index entry
        content: Content/description for search indexing
        fname: Filename for the index entry (e.g., "book_12345")
        vue_route: Vue.js route path (e.g., "book/12345")
    """
    redirect_url = f"../index.html#/{vue_route}"
    html_content = (
        f"<html><head><title>{title}</title>"
        f'<meta http-equiv="refresh" content="0;URL=\'{redirect_url}\'" />'
        f"</head><body></body></html>"
    )

    logger.debug(f"Adding {fname} to ZIM index")
    Global.add_item_for(
        title=title,
        path=f"index/{fname}",
        content=html_content,
        mimetype="text/html",
        index_data=IndexData(title=title, content=content),
    )


def generate_json_files(
    zim_name: str,
    formats: list[str],
    title: str | None = None,
    description: str | None = None,
    *,
    add_lcc_shelves: bool = False,
) -> None:
    """Generate all JSON files for Vue.js frontend"""
    logger.info("Generating JSON files for Vue.js UI")

    logger.info("Generating high-level JSON files")
    logger.debug("Generating books.json")
    books_preview = [_book_to_preview(book) for book in repository.get_all_books()]
    books_collection = Books(books=books_preview, total_count=len(books_preview))
    Global.add_item_for(
        path="books.json",
        content=books_collection.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    logger.debug("Generating authors.json")
    authors_preview = [
        _author_to_preview(author) for author in repository.get_all_authors()
    ]
    authors_collection = Authors(
        authors=authors_preview, total_count=len(authors_preview)
    )
    Global.add_item_for(
        path="authors.json",
        content=authors_collection.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    if add_lcc_shelves:
        logger.debug("Generating lcc_shelves.json")
        shelves_preview = [
            _lcc_shelf_to_preview(shelf_code)
            for shelf_code in repository.get_lcc_shelves()
        ]
        shelves_collection = LCCShelves(
            shelves=shelves_preview, total_count=len(shelves_preview)
        )
        Global.add_item_for(
            path="lcc_shelves.json",
            content=shelves_collection.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

    logger.debug("Generating config.json")
    config = Config(
        title=title or zim_name or "Project Gutenberg Library",
        description=description,
        main_color=None,
        secondary_color=None,
    )
    Global.add_item_for(
        path="config.json",
        content=config.model_dump_json(by_alias=True, indent=2),
        mimetype="application/json",
        is_front=False,
    )

    logger.info("Generating detail JSON files")
    logger.debug("Generating book detail files and index entries")
    for book in repository.get_all_books():
        book_detail = _book_to_schema(book, formats)
        Global.add_item_for(
            path=f"books/{book.book_id}.json",
            content=book_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

        # Add index entry for book
        book_description = book_detail.description or f"Book by {book.author.name()}"
        add_index_entry(
            title=book.title,
            content=book_description,
            fname=f"book_{book.book_id}",
            vue_route=f"book/{book.book_id}",
        )

    logger.debug("Generating author detail files and index entries")
    for author in repository.get_all_authors():
        author_books = [
            _book_to_preview(book)
            for book in repository.get_all_books()
            if book.author.gut_id == author.gut_id
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

        Global.add_item_for(
            path=f"authors/{author.gut_id}.json",
            content=author_detail.model_dump_json(by_alias=True, indent=2),
            mimetype="application/json",
            is_front=False,
        )

        # Add index entry for author
        author_content = f"Author: {author.name()}"
        if author.birth_year or author.death_year:
            lifespan_parts = []
            if author.birth_year:
                lifespan_parts.append(author.birth_year)
            lifespan_parts.append("-")
            if author.death_year:
                lifespan_parts.append(author.death_year)
            author_content += f" ({' '.join(lifespan_parts)})"
        author_content += f". {len(author_books)} book(s) available."

        add_index_entry(
            title=author.name(),
            content=author_content,
            fname=f"author_{author.gut_id}",
            vue_route=f"author/{author.gut_id}",
        )

    if add_lcc_shelves:
        logger.debug("Generating LCC shelf detail files and index entries")
        for shelf_code in repository.get_lcc_shelves():
            shelf_books = [
                _book_to_preview(book)
                for book in repository.get_all_books()
                if book.lcc_shelf == shelf_code
            ]
            shelf_detail = LCCShelf(
                code=shelf_code,
                name=None,
                books=shelf_books,
                book_count=len(shelf_books),
            )
            Global.add_item_for(
                path=f"lcc_shelves/{shelf_code}.json",
                content=shelf_detail.model_dump_json(by_alias=True, indent=2),
                mimetype="application/json",
                is_front=False,
            )

            shelf_title = f"LCC Shelf {shelf_code}"
            shelf_content = (
                f"Library of Congress Classification shelf {shelf_code} "
                f"with {len(shelf_books)} book(s)."
            )

            add_index_entry(
                title=shelf_title,
                content=shelf_content,
                fname=f"lcc_shelf_{shelf_code}",
                vue_route=f"lcc-shelf/{shelf_code}",
            )

    logger.info("JSON file generation completed")


def export_infobox_assets() -> None:
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
        if file_path.exists():
            logger.debug(f"Adding {zim_path} to ZIM")
            Global.add_item_for(
                path=zim_path,
                fpath=file_path,
                mimetype=mimetype,
                is_front=False,
            )


def generate_noscript_pages(
    formats: list[str],
) -> None:
    """Generate No-JavaScript fallback HTML pages"""
    logger.info("Generating No-JS fallback pages")

    # Add common CSS file to ZIM
    common_css_path = Path(__file__).parent / "templates" / "noscript" / "common.css"
    if common_css_path.exists():
        logger.debug("Adding noscript/common.css to ZIM")
        Global.add_item_for(
            path="noscript/common.css",
            fpath=common_css_path,
            mimetype="text/css",
            is_front=False,
        )
    all_books = repository.get_all_books()
    all_authors = repository.get_all_authors()
    shelves = sorted(repository.get_lcc_shelves())
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
    Global.add_item_for(
        path="noscript/books.html",
        content=books_html,
        mimetype="text/html",
        is_front=False,
        title="All Books - Project Gutenberg",
        auto_index=True,
    )

    # Generate authors listing page
    logger.debug("Generating noscript/authors.html")
    # Pre-calculate book counts per author
    author_book_counts = {}
    for author in all_authors:
        author_book_counts[author.gut_id] = sum(
            1 for book in all_books if book.author.gut_id == author.gut_id
        )
    authors_template = jinja_env.get_template("noscript/authors.html")
    authors_html = authors_template.render(
        authors=all_authors,
        all_books=all_books,
        author_book_counts=author_book_counts,
    )
    Global.add_item_for(
        path="noscript/authors.html",
        content=authors_html,
        mimetype="text/html",
        is_front=False,
        title="All Authors - Project Gutenberg",
        auto_index=True,
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
    Global.add_item_for(
        path="noscript/lcc_shelves.html",
        content=shelves_html,
        mimetype="text/html",
        is_front=False,
        title="LCC Shelves - Project Gutenberg",
        auto_index=True,
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
        Global.add_item_for(
            path=f"noscript/lcc_shelf_{shelf_code}.html",
            content=shelf_html,
            mimetype="text/html",
            is_front=False,
            title=f"LCC Shelf {shelf_code}",
            auto_index=True,
        )

    # Generate individual book pages
    logger.debug("Generating No-JS book detail pages")
    book_template = jinja_env.get_template("noscript/book.html")
    for book in all_books:
        book_html = book_template.render(
            book=book,
            formats=formats,
        )
        Global.add_item_for(
            path=f"noscript/book_{book.book_id}.html",
            content=book_html,
            mimetype="text/html",
            is_front=False,
            title=book.title,
            auto_index=True,
        )

    # Generate individual author pages
    logger.debug("Generating No-JS author pages")
    author_template = jinja_env.get_template("noscript/author.html")
    for author in all_authors:
        author_books = [
            book for book in all_books if book.author.gut_id == author.gut_id
        ]
        author_html = author_template.render(
            author=author,
            author_books=author_books,
        )
        Global.add_item_for(
            path=f"noscript/author_{author.gut_id}.html",
            content=author_html,
            mimetype="text/html",
            is_front=False,
            title=author.name(),
            auto_index=True,
        )

    logger.info("No-JS fallback pages generation completed")
