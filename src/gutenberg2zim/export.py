import json
import urllib.parse
from collections.abc import Iterable
from pathlib import Path

import bs4
from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, PackageLoader

import gutenberg2zim
from gutenberg2zim.constants import LOCALES_LOCATION, logger
from gutenberg2zim.iso639 import language_name
from gutenberg2zim.models import Book, repository
from gutenberg2zim.shared import Global
from gutenberg2zim.utils import (
    UTF8,
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    fname_for,
    get_lang_groups,
    get_langs_with_count,
    read_file,
    save_file,
)

jinja_env = Environment(  # noqa: S701
    loader=PackageLoader("gutenberg2zim", "templates")
)

DEBUG_COUNT = []


def get_ui_languages_for():
    ui_languages = ["en", "fr", "de", "it", "ar", "nl", "es", "pt"]
    languages = get_langs_with_count(languages=None)
    if len(languages) == 1 and languages[-1][1] in ui_languages:
        return [languages[-1][1]]
    return ui_languages


def get_default_context(project_id):
    if not Global.default_context or Global.default_context_project_id != project_id:
        Global.default_context_project_id = project_id
        l10n_strings = {"default_locale": "en", "locales": {}}
        for file in LOCALES_LOCATION.glob("*.json"):
            if not file.is_file():
                continue
            locale_data = json.loads(file.read_bytes())
            if "ui_strings" not in locale_data:
                continue
            l10n_strings["locales"][file.stem] = locale_data["ui_strings"]
        Global.default_context = {
            "l10n_strings": json.dumps(l10n_strings),
            "ui_languages": get_ui_languages_for(),
            "languages": get_langs_with_count(languages=None),
            "project_id": project_id,
        }
    return Global.default_context.copy()


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


def tmpl_path() -> Path:
    return Path(gutenberg2zim.__file__).parent / "templates"


def get_list_of_all_languages():
    # Get all unique languages from all books
    languages = set()
    for book in repository.books.values():
        languages.update(book.languages)
    return list(languages)


def export_skeleton(
    project_id,
    title_search,
    add_lcc_shelves,
):
    context = get_default_context(project_id)
    context.update(
        {
            "show_books": True,
            "title_search": title_search,
            "add_lcc_shelves": add_lcc_shelves,
        }
    )

    # js/l10n.js is a template (includes list of avail languages)
    rendered = jinja_env.get_template("js/l10n.js").render(**context)
    Global.add_item_for(
        path="js/l10n.js",
        content=rendered,
        mimetype="text/javascript",
        is_front=True,
    )

    # add CSS/JS/* to zim
    src_folder = tmpl_path()
    for fname in (
        "css",
        "js",
        "jquery",
        "favicon.ico",
        "favicon.png",
        "jquery-ui",
        "datatables",
        "fonts",
    ):
        assets_root = src_folder / fname

        # recursively add our assets, at a path identical to position in repo
        if assets_root.is_file():
            Global.add_item_for(path=fname, fpath=assets_root)
        else:
            for fpath in assets_root.glob("**/*"):
                if not fpath.is_file() or fpath.name == "l10n.js":
                    continue
                path = str(fpath.relative_to(assets_root))
                Global.add_item_for(path=str(Path(fname) / path), fpath=fpath)

    # export homepage
    template = jinja_env.get_template("Home.html")
    rendered = template.render(**context)
    Global.add_item_for(
        path="Home",
        content=rendered,
        mimetype="text/html",
        is_front=True,
    )


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
    for meta in soup.findAll("meta"):
        if "charset" in meta.attrs:
            encoding_specified = True
            # logger.debug("found <meta> tag with charset `{}`"
            #              .format(meta.attrs.get('charset')))
            del meta.attrs["charset"]
        elif "content" in meta.attrs and "charset=" in meta.attrs.get("content"):
            try:
                ctype, _ = meta.attrs.get("content").split(";", 1)
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
        for img in soup.findAll("img"):
            if "src" in img.attrs:
                img.attrs["src"] = img.attrs["src"].replace(
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
        for link in soup.findAll("a"):
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
            sum([1 for e in body.children if not isinstance(e, bs4.NavigableString)])
            == 1
        )
    except Exception:
        is_encapsulated_in_div = False

    if is_encapsulated_in_div and not epub:
        DEBUG_COUNT.append((book.book_id, book.title))

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


def cover_html_content_for(
    book,
    project_id,
    title_search,
    add_lcc_shelves,
    formats,
    *,
    has_cover: bool,
):
    cover_img = f"{book.book_id}_cover_image.jpg" if has_cover else None

    translate_author = (
        f' data-l10n-id="author-{book.author.name().lower()}"'
        if book.author.name() in ["Anonymous", "Various"]
        else ""
    )

    # Convert license string to slug format for translation
    # "Public domain in the USA." -> "PD", "Copyright" -> "Copyright"
    license_slug = "PD" if "public domain" in book.license.lower() else "Copyright"
    translate_license = (
        f' data-l10n-id="license-{license_slug.lower()}"'
        if license_slug in ["PD", "Copyright"]
        else ""
    )

    # book.languages is now a list[str] directly
    book_languages = sorted(book.languages)

    context = get_default_context(project_id=project_id)
    context.update(
        {
            "book": book,
            "cover_img": cover_img,
            "book_languages": book_languages,
            "formats": book.requested_formats(formats),
            "translate_author": translate_author,
            "translate_license": translate_license,
            "title_search": title_search,
            "add_lcc_shelves": add_lcc_shelves,
        }
    )
    template = jinja_env.get_template("cover_article.html")
    return template.render(**context)


def author_html_content_for(author, project_id):
    context = get_default_context(project_id=project_id)
    context.update({"author": author})
    template = jinja_env.get_template("author.html")
    return template.render(**context)


def save_author_file(author, project_id):
    logger.debug(f"\t\tSaving author file {author.name()} (ID {author})")
    Global.add_item_for(
        path=f"{author.fname()}",
        content=author_html_content_for(author, project_id),
        mimetype="text/html",
        is_front=True,
    )


def export_book(
    book: Book,
    book_files: dict[str, bytes],
    cover_image: bytes | None,
    formats: list[str],
    project_id: str,
    *,
    title_search: bool,
    add_lcc_shelves: bool,
):
    """Export book to ZIM using in-memory content"""
    logger.debug(f"Exporting book {book.book_id}")
    handle_book_files(
        book=book,
        book_files=book_files,
        formats=formats,
    )

    write_book_presentation_article(
        book=book,
        cover_image=cover_image,
        project_id=project_id,
        title_search=title_search,
        add_lcc_shelves=add_lcc_shelves,
        formats=formats,
    )


def handle_book_files(
    book: Book,
    book_files: dict[str, bytes],
    formats: list[str],
):
    """Handle book files from in-memory content and add to ZIM"""
    logger.debug(f"\tExporting Book #{book.book_id}.")

    # Find the main HTML file
    main_html_filename = f"{book.book_id}.html"
    html_content = None

    if main_html_filename in book_files:
        html_content = book_files[main_html_filename].decode("utf-8", errors="replace")

    if html_content:
        article_name = article_name_for(book)
        logger.debug(f"\t\tProcessing HTML content for {article_name}")
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
            logger.debug(f"\t\tProcessing companion HTML: {filename}")
            try:
                html_str = file_content.decode("utf-8", errors="replace")
                new_html = update_html_for_static(
                    book=book, html_content=html_str, formats=formats
                )
                Global.add_item_for(
                    path=filename,
                    content=str(new_html),
                    mimetype="text/html",
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
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling file {filename}: {e}")


def write_book_presentation_article(
    book,
    cover_image: bytes | None,
    project_id,
    title_search,
    add_lcc_shelves,
    formats,
):
    """Write book presentation article directly to ZIM"""
    article_name = article_name_for(book=book, cover=True)
    logger.debug("\t\tExporting article presentation")

    # Add cover image to ZIM if available
    if cover_image:
        cover_path = f"covers/{book.book_id}_cover_image.jpg"
        Global.add_item_for(
            path=cover_path,
            content=cover_image,
            mimetype="image/jpeg",
        )

    html = cover_html_content_for(
        book=book,
        has_cover=cover_image is not None,
        project_id=project_id,
        title_search=title_search,
        add_lcc_shelves=add_lcc_shelves,
        formats=formats,
    )

    Global.add_item_for(
        path=article_name,
        content=html,
        mimetype="text/html",
    )


def _lcc_shelf_list_for_books(books: Iterable[Book]):
    return sorted({book.lcc_shelf for book in books if book.lcc_shelf})


def lcc_shelf_list():
    return _lcc_shelf_list_for_books(repository.get_all_books())


def lcc_shelf_list_language(lang):
    return _lcc_shelf_list_for_books(
        filter(lambda book: lang in book.languages, repository.get_all_books())
    )


def export_to_json_helpers(languages, formats, project_id, add_lcc_shelves):
    def dumpjs(col, fn, var="json_data"):
        Global.add_item_for(
            path=fn,
            content=f"var {var} = {json.dumps(col)};",
            mimetype="text/javascript",
            is_front=False,
        )

    # all books sorted by popularity
    logger.info("\tDumping full_by_popularity.js")
    dumpjs(
        [
            book.to_array(all_requested_formats=formats)
            for book in sorted(
                repository.get_all_books(),
                key=lambda book: book.downloads,
                reverse=True,
            )
        ],
        "full_by_popularity.js",
    )

    # all books sorted by title
    logger.info("\tDumping full_by_title.js")
    dumpjs(
        [
            book.to_array(all_requested_formats=formats)
            for book in sorted(repository.get_all_books(), key=lambda book: book.title)
        ],
        "full_by_title.js",
    )

    # language-specific collections
    logger.info("\tDumping lang_xxx and authors_lang_xxx files")
    for lang in languages:
        # by popularity
        logger.debug(f"\t\tDumping lang_{lang}_by_popularity.js")

        dumpjs(
            [
                book.to_array(all_requested_formats=formats)
                for book in sorted(
                    filter(
                        lambda book: lang in book.languages, repository.get_all_books()
                    ),
                    key=lambda book: book.downloads,
                    reverse=True,
                )
            ],
            f"lang_{lang}_by_popularity.js",
        )

        # by title
        logger.debug(f"\t\tDumping lang_{lang}_by_title.js")
        dumpjs(
            [
                book.to_array(all_requested_formats=formats)
                for book in sorted(
                    filter(
                        lambda book: lang in book.languages, repository.get_all_books()
                    ),
                    key=lambda book: book.title,
                )
            ],
            f"lang_{lang}_by_title.js",
        )

        # Get unique authors for books in this language
        logger.debug(f"\t\tDumping authors_lang_{lang}.js")
        dumpjs(
            [
                author.to_array()
                for author in {
                    book.author
                    for book in repository.get_all_books()
                    if lang in book.languages
                }
            ],
            f"authors_lang_{lang}.js",
            "authors_json_data",
        )

    if add_lcc_shelves:
        logger.info("\tDumping LCC shelves_xxx JS and HTML files")
        for lcc_shelf in lcc_shelf_list():
            # dumpjs for LCC shelf by popularity
            # this will allow the popularity button to use this js on the
            # particular shelf page
            logger.debug(f"\t\tDumping lcc_shelf_{lcc_shelf}_by_popularity.js")
            dumpjs(
                [
                    book.to_array(all_requested_formats=formats)
                    for book in sorted(
                        [
                            book
                            for book in repository.get_all_books()
                            if book.lcc_shelf == lcc_shelf
                        ],
                        key=lambda b: b.downloads,
                        reverse=True,
                    )
                ],
                f"lcc_shelf_{lcc_shelf}_by_popularity.js",
            )

            # by title
            logger.debug(f"\t\tDumping lcc_shelf_{lcc_shelf}_by_title.js")
            dumpjs(
                [
                    book.to_array(all_requested_formats=formats)
                    for book in sorted(
                        [
                            book
                            for book in repository.get_all_books()
                            if book.lcc_shelf == lcc_shelf
                        ],
                        key=lambda b: b.title,
                    )
                ],
                f"lcc_shelf_{lcc_shelf}_by_title.js",
            )

            # by language
            for lang in languages:
                logger.debug(
                    f"\t\tDumping lcc_shelf_{lcc_shelf}_lang_{lang}_by_popularity.js"
                )
                dumpjs(
                    [
                        book.to_array(all_requested_formats=formats)
                        for book in sorted(
                            [
                                book
                                for book in repository.get_all_books()
                                if book.lcc_shelf == lcc_shelf
                                and lang in book.languages
                            ],
                            key=lambda b: b.downloads,
                            reverse=True,
                        )
                    ],
                    f"lcc_shelf_{lcc_shelf}_lang_{lang}_by_popularity.js",
                )

                logger.debug(
                    f"\t\tDumping lcc_shelf_{lcc_shelf}_lang_{lang}_by_title.js"
                )
                dumpjs(
                    [
                        book.to_array(all_requested_formats=formats)
                        for book in sorted(
                            [
                                book
                                for book in repository.get_all_books()
                                if book.lcc_shelf == lcc_shelf
                                and lang in book.languages
                            ],
                            key=lambda b: b.title,
                        )
                    ],
                    f"lcc_shelf_{lcc_shelf}_lang_{lang}_by_title.js",
                )

        # dump all LCC shelves from any given language
        for lang in languages:
            logger.debug(f"\t\tDumping lcc_shelves_lang_{lang}.js")
            dumpjs(lcc_shelf_list_language(lang), f"lcc_shelves_lang_{lang}.js")

        logger.debug("\t\tDumping lcc_shelves.js")
        dumpjs(lcc_shelf_list(), "lcc_shelves.js", "lcc_shelves_json_data")

        # Create the LCC shelf home page
        logger.debug("\t\tDumping lcc_shelf_home (HTML)")
        context = get_default_context(project_id=project_id)
        context.update({"lcc_shelf_home": True, "add_lcc_shelves": True})
        template = jinja_env.get_template("lcc_shelf_home.html")
        rendered = template.render(**context)
        Global.add_item_for(
            path="lcc_shelf_home",
            content=rendered,
            mimetype="text/html",
            is_front=False,
        )

        # add individual LCC shelf pages
        for lcc_shelf in lcc_shelf_list():
            if lcc_shelf is None:
                continue
            logger.debug(f"Dumping lcc_shelf_{lcc_shelf} (HTML)")
            context["lcc_shelf"] = lcc_shelf
            context.update(
                {
                    "show_books": True,
                    "lcc_shelf_home": False,
                    "individual_lcc_shelf": True,
                    "no_filters": True,
                    "add_lcc_shelves": True,
                }
            )
            template = jinja_env.get_template("lcc_shelf.html")
            rendered = template.render(**context)
            Global.add_item_for(
                path=f"lcc_shelf_{lcc_shelf}",
                content=rendered,
                mimetype="text/html",
                is_front=False,
            )

    # author specific collections
    logger.info("\tDumping authors_xxx JS files")

    for author in repository.get_all_authors():
        # Get all books by this author
        author_books = [
            book
            for book in repository.get_all_books()
            if book.author.gut_id == author.gut_id
        ]

        # by popularity
        logger.debug(f"\t\tDumping auth_{author.gut_id}_by_popularity.js")
        author_books_by_pop = sorted(
            author_books, key=lambda b: b.downloads, reverse=True
        )
        dumpjs(
            [
                book.to_array(all_requested_formats=formats)
                for book in author_books_by_pop
            ],
            f"auth_{author.gut_id}_by_popularity.js",
        )

        # by title
        logger.debug(f"\t\tDumping auth_{author.gut_id}_by_title.js")
        author_books_by_title = sorted(author_books, key=lambda b: b.title)
        dumpjs(
            [
                book.to_array(all_requested_formats=formats)
                for book in author_books_by_title
            ],
            f"auth_{author.gut_id}_by_title.js",
        )

        # by language
        for lang in languages:
            logger.debug(f"\t\tDumping auth_{author.gut_id}_by_lang_{lang}.js")

            author_books_lang = [
                book
                for book in repository.get_all_books()
                if book.author.gut_id == author.gut_id and lang in book.languages
            ]

            author_books_lang_by_pop = sorted(
                author_books_lang, key=lambda b: b.downloads, reverse=True
            )
            dumpjs(
                [
                    book.to_array(all_requested_formats=formats)
                    for book in author_books_lang_by_pop
                ],
                f"auth_{author.gut_id}_lang_{lang}_by_popularity.js",
            )

            author_books_lang_by_title = sorted(
                author_books_lang, key=lambda b: b.title
            )
            dumpjs(
                [
                    book.to_array(all_requested_formats=formats)
                    for book in author_books_lang_by_title
                ],
                f"auth_{author.gut_id}_lang_{lang}_by_title.js",
            )

        # author HTML redirect file
        save_author_file(author, project_id)

    # authors list sorted by name
    logger.info("\tDumping authors.js")
    dumpjs(
        [author.to_array() for author in repository.get_all_authors()],
        "authors.js",
        "authors_json_data",
    )

    # languages list sorted by code
    logger.info("\tDumping languages.js")
    avail_langs = get_langs_with_count(languages)
    dumpjs(avail_langs, "languages.js", "languages_json_data")

    # languages by weight
    main_languages, other_languages = get_lang_groups()
    logger.info("\tDumping main_languages.js and other_languages.js")
    dumpjs(main_languages, "main_languages.js", "main_languages_json_data")
    dumpjs(other_languages, "other_languages.js", "other_languages_json_data")
