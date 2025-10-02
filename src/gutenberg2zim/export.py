import json
import urllib.parse
from multiprocessing.dummy import Pool
from pathlib import Path
from typing import Any

import bs4
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader

import gutenberg2zim
from gutenberg2zim.constants import TMP_FOLDER_PATH, logger
from gutenberg2zim.database import Author, Book, BookLanguage
from gutenberg2zim.iso639 import language_name
from gutenberg2zim.l10n import l10n_strings
from gutenberg2zim.scraper_progress import ScraperProgress
from gutenberg2zim.shared import Global
from gutenberg2zim.utils import (
    UTF8,
    archive_name_for,
    article_name_for,
    book_name_for_fs,
    critical_error,
    fname_for,
    get_lang_groups,
    get_langs_with_count,
    get_list_of_filtered_books,
    read_file,
    save_file,
)

jinja_env = Environment(  # noqa: S701
    loader=PackageLoader("gutenberg2zim", "templates")
)

DEBUG_COUNT = []
NB_POPULARITY_STARS = 5


def get_ui_languages_for(books_ids):
    ui_languages = ["en", "fr", "de", "it", "ar", "nl", "es", "pt"]
    languages = get_langs_with_count(books_ids=books_ids)
    if len(languages) == 1 and languages[-1][1] in ui_languages:
        return [languages[-1][1]]
    return ui_languages


def get_default_context(project_id, books_ids):
    if not Global.default_context or Global.default_context_project_id != project_id:
        Global.default_context_project_id = project_id
        Global.default_context = {
            "l10n_strings": json.dumps(l10n_strings),
            "ui_languages": get_ui_languages_for(books_ids=books_ids),
            "languages": get_langs_with_count(books_ids=books_ids),
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
    return list(
        {bl.language_code for bl in BookLanguage.select(BookLanguage.language_code)}
    )


def export_skeleton(
    project_id,
    books_ids,
    title_search,
    add_bookshelves,
):
    context = get_default_context(project_id, books_ids)
    context.update(
        {
            "show_books": True,
            "title_search": title_search,
            "add_bookshelves": add_bookshelves,
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
    tpl_path = "Home.html"
    template = jinja_env.get_template(tpl_path)
    rendered = template.render(**context)
    Global.add_item_for(
        path=tpl_path,
        content=rendered,
        mimetype="text/html",
        is_front=True,
    )


def export_all_books(
    project_id: str,
    download_cache: Path,
    concurrency: int,
    languages: list[str],
    formats: list[str],
    only_books: list[int],
    progress: ScraperProgress,
    *,
    force: bool,
    title_search: bool,
    add_bookshelves: bool,
) -> None:
    books_ids: Any = [
        book.book_id
        for book in get_list_of_filtered_books(
            languages=languages, formats=formats, only_books=only_books
        )
    ]

    logger.info(f"Found {len(books_ids)} books for export")

    if not len(get_langs_with_count(books_ids=books_ids)):
        critical_error(
            "Unable to proceed. Combination of languages, "
            "books and formats has no result."
        )

    # export to JSON helpers
    logger.info("Exporting JSON helpers")
    export_to_json_helpers(
        books_ids=books_ids,
        languages=languages,
        formats=formats,
        project_id=project_id,
        add_bookshelves=add_bookshelves,
    )

    # export HTML index and other static files
    logger.info("Exporting HTML skeleton")
    export_skeleton(
        books_ids=books_ids,
        project_id=project_id,
        title_search=title_search,
        add_bookshelves=add_bookshelves,
    )

    # Compute popularity
    logger.info("Computing book popularity")
    popbooks = (
        Book.select()
        .where(not books_ids or Book.book_id << books_ids)
        .order_by(Book.downloads.desc())
    )
    popbooks_count = popbooks.count()
    stars_limits = [0] * NB_POPULARITY_STARS
    stars = NB_POPULARITY_STARS
    nb_downloads = popbooks[0].downloads
    for ibook in range(0, popbooks.count(), 1):
        if (
            ibook
            > float(NB_POPULARITY_STARS - stars + 1)
            / NB_POPULARITY_STARS
            * popbooks_count
            and popbooks[ibook].downloads < nb_downloads
        ):
            stars_limits[stars - 1] = nb_downloads
            stars = stars - 1
        nb_downloads = popbooks[ibook].downloads

    for book in Book.select().where(not books_ids or Book.book_id << books_ids):
        book.popularity = sum(
            [int(book.downloads >= stars_limits[i]) for i in range(NB_POPULARITY_STARS)]
        )

    logger.info(f"Exporting books with {concurrency} (parallel) worker(s)")

    def dlb(b):
        export_book(
            b,
            download_cache=download_cache,
            formats=formats,
            books_ids=books_ids,
            project_id=project_id,
            force=force,
            title_search=title_search,
            add_bookshelves=add_bookshelves,
        )
        progress.increase_progress()

    Pool(concurrency).map(
        dlb, Book.select().where(not books_ids or Book.book_id << books_ids)
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
    soup = BeautifulSoup(html_content, "lxml-html")

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
            head = soup.find("head")
            if not head:
                head = soup.new_tag("head")
                soup.html.insert(0, head)  # type: ignore
            head.append(soup.new_tag("title"))
            soup.title.string = book.title  # type: ignore

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
    try:
        is_encapsulated_in_div = (
            sum(
                [
                    1
                    for e in body.children  # type: ignore
                    if not isinstance(e, bs4.NavigableString)
                ]
            )
            == 1
        )
    except Exception:
        is_encapsulated_in_div = False

    if is_encapsulated_in_div and not epub:
        DEBUG_COUNT.append((book.book_id, book.title))

    if not is_encapsulated_in_div:
        for start_of_text, end_of_text in patterns:
            if (
                start_of_text not in body.text  # type: ignore
                and end_of_text not in body.text  # type: ignore
            ):
                continue

            if start_of_text in body.text and end_of_text in body.text:  # type: ignore
                remove = True
                for child in body.children:  # type: ignore
                    if isinstance(child, bs4.NavigableString):
                        continue
                    if end_of_text in getattr(child, "text", ""):
                        remove = True
                    if start_of_text in getattr(child, "text", ""):
                        child.decompose()  # type: ignore
                        remove = False
                    if remove:
                        child.decompose()  # type: ignore
                break

            elif start_of_text in body.text:  # type: ignore
                # logger.debug("FOUND START: {}".format(start_of_text))
                remove = True
                for child in body.children:  # type: ignore
                    if isinstance(child, bs4.NavigableString):
                        continue
                    if start_of_text in getattr(child, "text", ""):
                        child.decompose()  # type: ignore
                        remove = False
                    if remove:
                        child.decompose()  # type: ignore
                break
            elif end_of_text in body.text:  # type: ignore
                # logger.debug("FOUND END: {}".format(end_of_text))
                remove = False
                for child in body.children:  # type: ignore
                    if isinstance(child, bs4.NavigableString):
                        continue
                    if end_of_text in getattr(child, "text", ""):
                        remove = True
                    if remove:
                        child.decompose()  # type: ignore
                break

    # build infobox
    if not epub:
        infobox = jinja_env.get_template("book_infobox.html")
        infobox_html = infobox.render({"book": book, "formats": formats})
        info_soup = BeautifulSoup(infobox_html, "lxml-html")
        body.insert(0, info_soup.find("div"))  # type: ignore

    # if there is no charset, set it to utf8
    if not epub:
        meta = BeautifulSoup(
            '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />',
            "lxml-html",
        )
        head = soup.find("head")
        html = soup.find("html")
        if head:
            head.insert(0, meta.head.contents[0])  # type: ignore
        elif html:
            html.insert(0, meta.head)  # type: ignore
        else:
            soup.insert(0, meta.head)  # type: ignore

        return html

    return soup


def cover_html_content_for(
    book, cover_dir, books_ids, project_id, title_search, add_bookshelves, formats
):
    cover_img = f"{book.book_id}_cover_image.jpg"
    cover_img = cover_img if (cover_dir / cover_img).exists() else None

    translate_author = (
        f' data-l10n-id="author-{book.author.name().lower()}"'
        if book.author.name() in ["Anonymous", "Various"]
        else ""
    )

    translate_license = (
        f' data-l10n-id="license-{book.book_license.slug.lower()}"'
        if book.book_license.slug in ["PD", "Copyright"]
        else ""
    )

    book_languages = [
        lang.language_code for lang in book.languages.order_by(BookLanguage.id)  # type: ignore
    ]

    context = get_default_context(project_id=project_id, books_ids=books_ids)
    context.update(
        {
            "book": book,
            "cover_img": cover_img,
            "book_languages": book_languages,
            "formats": book.requested_formats(formats),
            "translate_author": translate_author,
            "translate_license": translate_license,
            "title_search": title_search,
            "add_bookshelves": add_bookshelves,
        }
    )
    template = jinja_env.get_template("cover_article.html")
    return template.render(**context)


def author_html_content_for(author, books_ids, project_id):
    context = get_default_context(project_id=project_id, books_ids=books_ids)
    context.update({"author": author})
    template = jinja_env.get_template("author.html")
    return template.render(**context)


def save_author_file(author, books_ids, project_id):
    logger.debug(f"\t\tSaving author file {author.name()} (ID {author})")
    Global.add_item_for(
        path=f"{author.fname()}.html",
        content=author_html_content_for(author, books_ids, project_id),
        mimetype="text/html",
        is_front=True,
    )


def export_book(
    book: Book,
    download_cache: Path,
    formats: list[str],
    books_ids: list[int],
    project_id: str,
    *,
    force: bool,
    title_search: bool,
    add_bookshelves: bool,
):
    logger.debug(f"Exporting book {book.book_id}")
    book_dir = download_cache / str(book.book_id)
    cover_dir = download_cache / "covers"
    handle_book_files(
        book=book,
        src_dir=book_dir,
        cover_dir=cover_dir,
        formats=formats,
        force=force,
    )

    write_book_presentation_article(
        book=book,
        cover_dir=cover_dir,
        force=force,
        project_id=project_id,
        title_search=title_search,
        add_bookshelves=add_bookshelves,
        books_ids=books_ids,
        formats=formats,
    )


def handle_book_files(
    book: Book,
    src_dir: Path,
    cover_dir: Path,
    formats: list[str],
    *,
    force: bool,
):

    logger.debug(f"\tExporting Book #{book.book_id}.")

    # actual book content, as HTML
    html, _ = html_content_for(book=book, src_dir=src_dir)
    html_book_optimized_files = []
    if html:
        article_name = article_name_for(book)
        article_fpath = TMP_FOLDER_PATH / article_name
        if not article_fpath.exists() or force:
            logger.debug(f"\t\tExporting to {article_fpath}")
            try:
                new_html = update_html_for_static(
                    book=book, html_content=html, formats=formats
                )
            except Exception:
                raise
            save_bs_output(new_html, article_fpath, UTF8)
            html_book_optimized_files.append(article_fpath)
        else:
            logger.info(f"\t\tSkipping HTML article {article_fpath}")
        Global.add_item_for(path=article_name, fpath=article_fpath)

    def handle_companion_file(
        fname: Path,
        dstfname: str | None = None,
    ):
        src = fname
        if dstfname is None:
            dstfname = fname.name
        Global.add_item_for(path=dstfname, fpath=src)

    # associated files (images, etc)
    for fpath in src_dir.iterdir():
        if fpath.is_file() and fpath.name.startswith(f"{book.book_id}_"):
            if fpath.suffix in (".html", ".htm"):
                src = fpath
                dst = TMP_FOLDER_PATH / fpath.name
                if dst.exists() and not force:
                    logger.debug(f"\t\tSkipping already optimized HTML {dst}")
                    Global.add_item_for(path=fpath.name, fpath=dst)
                    continue

                logger.info(f"\tExporting HTML file to {dst}")
                html, _ = read_file(src)
                new_html = update_html_for_static(
                    book=book, html_content=html, formats=formats
                )
                save_bs_output(new_html, dst, UTF8)
                html_book_optimized_files.append(dst)
            else:
                try:
                    handle_companion_file(fname=fpath)
                except Exception as e:
                    logger.exception(e)
                    logger.error(f"\t\tException while handling companion file: {e}")

    # other formats
    for other_format in [
        fmt
        for fmt in formats
        if fmt != "html" and fmt not in str(book.unsupported_formats).split(",")
    ]:
        book_file = src_dir / fname_for(book, other_format)
        if book_file.exists():
            try:
                handle_companion_file(
                    fname=book_file,
                    dstfname=archive_name_for(book, other_format),
                )
            except Exception as e:
                logger.exception(e)
                logger.error(f"\t\tException while handling companion file: {e}")

    # cover image
    cover_img = cover_dir / f"{book.book_id}_cover_image.jpg"
    if cover_img.exists():
        handle_companion_file(
            fname=cover_img,
            dstfname=f"covers/{book.book_id}_cover_image.jpg",
        )


def write_book_presentation_article(
    book,
    cover_dir,
    force,
    project_id,
    title_search,
    add_bookshelves,
    books_ids,
    formats,
):
    article_name = article_name_for(book=book, cover=True)
    cover_fpath = TMP_FOLDER_PATH / article_name
    if not cover_fpath.exists() or force:
        logger.debug(f"\t\tExporting article presentation to {cover_fpath}")
        html = cover_html_content_for(
            book=book,
            cover_dir=cover_dir,
            books_ids=books_ids,
            project_id=project_id,
            title_search=title_search,
            add_bookshelves=add_bookshelves,
            formats=formats,
        )
        with open(cover_fpath, "w") as f:
            f.write(html)
    else:
        logger.debug(f"\t\tSkipping already optimized cover {cover_fpath}")

    Global.add_item_for(path=article_name, fpath=cover_fpath)


# Returns the list of all Bookshelves
# Ex: [None, u'Adventure', u"Children's Literature", u'Christianity',
# u'Detective Fiction', u'Gothic Fiction', u'Harvard Classics', u'Historical Fiction',
# u'Mathematics', u'Plays', u'School Stories', u'Science Fiction']
def bookshelf_list(books_ids):
    return [
        bookshelf.bookshelf
        for bookshelf in Book.select()
        .where(not books_ids or Book.book_id << books_ids)
        .order_by(Book.bookshelf.asc())
        .group_by(Book.bookshelf)
    ]


def bookshelf_list_language(lang, books_ids):
    return [
        book.bookshelf
        for book in Book.select(Book.bookshelf)
        .where(not books_ids or Book.book_id << books_ids)
        .join(BookLanguage)
        .where(BookLanguage.language_code == lang)
        .where(Book.bookshelf.is_null(False))
        .group_by(Book.bookshelf)
        .order_by(Book.bookshelf.asc())
    ]


def export_to_json_helpers(books_ids, languages, formats, project_id, add_bookshelves):
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
            for book in Book.select()
            .where(not books_ids or Book.book_id << books_ids)
            .order_by(Book.downloads.desc())
        ],
        "full_by_popularity.js",
    )

    # all books sorted by title
    logger.info("\tDumping full_by_title.js")
    dumpjs(
        [
            book.to_array(all_requested_formats=formats)
            for book in Book.select()
            .where(not books_ids or Book.book_id << books_ids)
            .order_by(Book.title.asc())
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
                for book in Book.select()
                .where(not books_ids or Book.book_id << books_ids)
                .join(BookLanguage)
                .where(BookLanguage.language_code == lang)
                .order_by(Book.downloads.desc())
            ],
            f"lang_{lang}_by_popularity.js",
        )
        # by title
        logger.debug(f"\t\tDumping lang_{lang}_by_title.js")
        dumpjs(
            [
                book.to_array(all_requested_formats=formats)
                for book in Book.select()
                .where(not books_ids or Book.book_id << books_ids)
                .join(BookLanguage)
                .where(BookLanguage.language_code == lang)
                .order_by(Book.title.asc())
            ],
            f"lang_{lang}_by_title.js",
        )

        logger.debug(f"\t\tDumping authors_lang_{lang}.js")
        dumpjs(
            [
                author.to_array()
                for author in Author.select()
                .join(Book)
                .where(not books_ids or Book.book_id << books_ids)
                .join(BookLanguage)
                .where(BookLanguage.language_code == lang)
                .distinct()
            ],
            f"authors_lang_{lang}.js",
            "authors_json_data",
        )

    if add_bookshelves:
        logger.info("\tDumping bookshelves_xxx JS and HTML files")
        bookshelves = bookshelf_list(books_ids)
        for bookshelf in bookshelves:
            # exclude the books with no bookshelf data
            if bookshelf is None:
                continue
            # dumpjs for bookshelf by popularity
            # this will allow the popularity button to use this js on the
            # particular bookshelf page
            logger.debug(f"\t\tDumping bookshelf_{bookshelf}_by_popularity.js")
            dumpjs(
                [
                    book.to_array(all_requested_formats=formats)
                    for book in Book.select()
                    .where(not books_ids or Book.book_id << books_ids)
                    .where(Book.bookshelf == bookshelf)
                    .order_by(Book.downloads.desc())
                ],
                f"bookshelf_{bookshelf}_by_popularity.js",
            )

            # by title
            logger.debug(f"\t\tDumping bookshelf_{bookshelf}_by_title.js")
            dumpjs(
                [
                    book.to_array(all_requested_formats=formats)
                    for book in Book.select()
                    .where(not books_ids or Book.book_id << books_ids)
                    .where(Book.bookshelf == bookshelf)
                    .order_by(Book.title.asc())
                ],
                f"bookshelf_{bookshelf}_by_title.js",
            )
            # by language
            for lang in languages:
                logger.debug(
                    f"\t\tDumping bookshelf_{bookshelf}_lang_{lang}_by_popularity.js"
                )

                dumpjs(
                    [
                        book.to_array(all_requested_formats=formats)
                        for book in Book.select()
                        .where(not books_ids or Book.book_id << books_ids)
                        .join(BookLanguage)
                        .where(BookLanguage.language_code == lang)
                        .where(Book.bookshelf == bookshelf)
                        .order_by(Book.downloads.desc())
                    ],
                    f"bookshelf_{bookshelf}_lang_{lang}_by_popularity.js",
                )

                logger.debug(
                    f"\t\tDumping bookshelf_{bookshelf}_lang_{lang}_by_title.js"
                )

                dumpjs(
                    [
                        book.to_array(all_requested_formats=formats)
                        for book in Book.select()
                        .where(not books_ids or Book.book_id << books_ids)
                        .join(BookLanguage)
                        .where(BookLanguage.language_code == lang)
                        .where(Book.bookshelf == bookshelf)
                        .order_by(Book.title.asc())
                    ],
                    f"bookshelf_{bookshelf}_lang_{lang}_by_title.js",
                )

        # dump all bookshelves from any given language
        for lang in languages:
            logger.debug(f"\t\tDumping bookshelves_lang_{lang}.js")
            temp = bookshelf_list_language(lang, books_ids)
            dumpjs(temp, f"bookshelves_lang_{lang}.js")

        logger.debug("\t\tDumping bookshelves.js")
        dumpjs(bookshelves, "bookshelves.js", "bookshelves_json_data")

        # Create the bookshelf home page
        logger.debug("\t\tDumping bookshelf_home.html")
        context = get_default_context(project_id=project_id, books_ids=books_ids)
        context.update({"bookshelf_home": True, "add_bookshelves": True})
        template = jinja_env.get_template("bookshelf_home.html")
        rendered = template.render(**context)
        Global.add_item_for(
            path="bookshelf_home.html",
            content=rendered,
            mimetype="text/html",
            is_front=False,
        )

        # add individual bookshelf pages
        for bookshelf in bookshelves:
            if bookshelf is None:
                continue
            logger.debug(f"Dumping {bookshelf}.html")
            context["bookshelf"] = bookshelf
            context.update(
                {
                    "show_books": True,
                    "bookshelf_home": False,
                    "individual_book_shelf": True,
                    "no_filters": True,
                    "add_bookshelves": True,
                }
            )
            template = jinja_env.get_template("bookshelf.html")
            rendered = template.render(**context)
            Global.add_item_for(
                path=f"{bookshelf}.html",
                content=rendered,
                mimetype="text/html",
                is_front=False,
            )

    # author specific collections
    logger.info("\tDumping authors_xxx JS files")
    authors = (
        Author.select()
        .join(Book)
        .where(not books_ids or Book.book_id << books_ids)
        .join(BookLanguage)
        .where(BookLanguage.language_code << languages)
        .distinct()
    )
    for author in authors:
        # by popularity
        logger.debug(f"\t\tDumping auth_{author.gut_id}_by_popularity.js")
        dumpjs(
            [
                book.to_array(all_requested_formats=formats)
                for book in Book.select()
                .where(not books_ids or Book.book_id << books_ids)
                .where(Book.author == author)
                .order_by(Book.downloads.desc())
            ],
            f"auth_{author.gut_id}_by_popularity.js",
        )
        # by title
        logger.debug(f"\t\tDumping auth_{author.gut_id}_by_title.js")
        dumpjs(
            [
                book.to_array(all_requested_formats=formats)
                for book in Book.select()
                .where(not books_ids or Book.book_id << books_ids)
                .where(Book.author == author)
                .order_by(Book.title.asc())
            ],
            f"auth_{author.gut_id}_by_title.js",
        )
        # by language
        for lang in languages:
            logger.debug(f"\t\tDumping auth_{author.gut_id}_by_lang_{lang}.js")

            dumpjs(
                [
                    book.to_array(all_requested_formats=formats)
                    for book in Book.select()
                    .where(not books_ids or Book.book_id << books_ids)
                    .join(BookLanguage)
                    .where(BookLanguage.language_code == lang)
                    .where(Book.author == author)
                    .order_by(Book.downloads.desc())
                ],
                f"auth_{author.gut_id}_lang_{lang}_by_popularity.js",
            )

            dumpjs(
                [
                    book.to_array(all_requested_formats=formats)
                    for book in Book.select()
                    .where(not books_ids or Book.book_id << books_ids)
                    .join(BookLanguage)
                    .where(BookLanguage.language_code == lang)
                    .where(Book.author == author)
                    .order_by(Book.title.asc())
                ],
                f"auth_{author.gut_id}_lang_{lang}_by_title.js",
            )

        # author HTML redirect file
        save_author_file(author, books_ids, project_id)

    # authors list sorted by name
    logger.info("\tDumping authors.js")
    dumpjs([author.to_array() for author in authors], "authors.js", "authors_json_data")

    # languages list sorted by code
    logger.info("\tDumping languages.js")
    avail_langs = get_langs_with_count(books_ids, languages)
    dumpjs(avail_langs, "languages.js", "languages_json_data")

    # languages by weight
    main_languages, other_languages = get_lang_groups(books_ids)
    logger.info("\tDumping main_languages.js and other_languages.js")
    dumpjs(main_languages, "main_languages.js", "main_languages_json_data")
    dumpjs(other_languages, "other_languages.js", "other_languages_json_data")
