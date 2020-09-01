#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import json
import zipfile
import tempfile
import urllib
import pathlib
import shutil

import six
from six import text_type
import bs4
from bs4 import BeautifulSoup
from path import Path as path
from jinja2 import Environment, PackageLoader
from multiprocessing.dummy import Pool

import gutenbergtozim
from gutenbergtozim import logger, TMP_FOLDER
from gutenbergtozim.utils import (
    FORMAT_MATRIX,
    main_formats_for,
    get_list_of_filtered_books,
    exec_cmd,
    get_langs_with_count,
    get_lang_groups,
    is_bad_cover,
    read_file,
    zip_epub,
    critical_error,
    save_file,
    UTF8,
    get_project_id,
    book_name_for_fs,
    archive_name_for,
    fname_for,
    article_name_for,
)
from gutenbergtozim.database import Book, Format, BookFormat, Author
from gutenbergtozim.iso639 import language_name
from gutenbergtozim.l10n import l10n_strings
from gutenbergtozim.s3 import upload_to_cache

jinja_env = Environment(loader=PackageLoader("gutenbergtozim", "templates"))

DEBUG_COUNT = []
NB_POPULARITY_STARS = 5


def get_ui_languages_for(books):
    ui_languages = ["en", "fr", "de", "it", "ar", "nl", "es"]
    languages = get_langs_with_count(books=books)
    if len(languages) == 1 and languages[-1][1] in ui_languages:
        return [languages[-1][1]]
    return ui_languages


def get_default_context(project_id, books):

    return {
        "l10n_strings": json.dumps(l10n_strings),
        "ui_languages": get_ui_languages_for(books),
        "languages": get_langs_with_count(books=books),
        "project_id": project_id,
    }


def fa_for_format(format):
    return {
        "html": "",
        "info": "fa-info-circle",
        "epub": "fa-download",
        "pdf": "fa-file-pdf-o",
    }.get(format, "fa-file-o")


def zim_link_prefix(format):
    return "../{}/".format({"html": "A", "epub": "I", "pdf": "I"}.get(format))


def urlencode(url):
    if six.PY2:
        return urllib.quote(url.encode(UTF8))
    else:
        return urllib.parse.quote(url)


def save_bs_output(soup, fpath, encoding=UTF8):
    save_file(soup if six.PY2 else str(soup), fpath, encoding)


jinja_env.filters["book_name_for_fs"] = book_name_for_fs
jinja_env.filters["zim_link_prefix"] = zim_link_prefix
jinja_env.filters["language_name"] = language_name
jinja_env.filters["fa_for_format"] = fa_for_format
jinja_env.filters["urlencode"] = urlencode


def tmpl_path():
    return os.path.join(path(gutenbergtozim.__file__).parent, "templates")


def get_list_of_all_languages():
    return list(set(list([b.language for b in Book.select(Book.language)])))


def export_skeleton(
    static_folder=None,
    dev_mode=False,
    languages=[],
    formats=[],
    only_books=[],
    title_search=False,
    add_bookshelves=False,
):

    # ensure dir exist
    path(static_folder).mkdir_p()

    project_id = get_project_id(
        languages=languages, formats=formats, only_books=only_books
    )

    books = get_list_of_filtered_books(
        languages=languages, formats=formats, only_books=only_books
    )

    # copy CSS/JS/* to static_folder
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
        src = os.path.join(src_folder, fname)
        dst = os.path.join(static_folder, fname)
        if not path(fname).ext:
            path(dst).rmtree_p()
            path(src).copytree(dst)
        else:
            path(src).copyfile(dst)

    # export homepage
    context = get_default_context(project_id, books=books)
    context.update(
        {
            "show_books": True,
            "dev_mode": dev_mode,
            "title_search": title_search,
            "add_bookshelves": add_bookshelves,
        }
    )
    for tpl_path in ("Home.html", "js/tools.js", "js/l10n.js"):
        template = jinja_env.get_template(tpl_path)
        rendered = template.render(**context)
        save_bs_output(rendered, os.path.join(static_folder, tpl_path), UTF8)


def export_all_books(
    static_folder=None,
    download_cache=None,
    concurrency=None,
    languages=[],
    formats=[],
    only_books=[],
    force=False,
    title_search=False,
    add_bookshelves=False,
    s3_storage=None,
    optimizer_version=None,
):

    project_id = get_project_id(
        languages=languages, formats=formats, only_books=only_books
    )

    # ensure dir exist
    path(static_folder).mkdir_p()

    books = get_list_of_filtered_books(
        languages=languages, formats=formats, only_books=only_books
    )

    if not len(get_langs_with_count(books=books)):
        critical_error(
            "Unable to proceed. Combination of lamguages, "
            "books and formats has no result."
        )

    # sz = len(list(books))
    # logger.debug("\tFiltered book collection size: {}".format(sz))

    def nb_by_fmt(fmt):
        return sum(
            [
                1
                for book in books
                if BookFormat.select(BookFormat, Book, Format)
                .join(Book)
                .switch(BookFormat)
                .join(Format)
                .where(Book.id == book.id)
                .where(Format.mime == FORMAT_MATRIX.get(fmt))
                .count()
            ]
        )

    logger.debug("\tFiltered book collection, PDF: {}".format(nb_by_fmt("pdf")))
    logger.debug("\tFiltered book collection, ePUB: {}".format(nb_by_fmt("epub")))
    logger.debug("\tFiltered book collection, HTML: {}".format(nb_by_fmt("html")))

    # export to JSON helpers
    export_to_json_helpers(
        books=books,
        static_folder=static_folder,
        languages=languages,
        formats=formats,
        project_id=project_id,
        title_search=title_search,
        add_bookshelves=add_bookshelves,
    )

    # export HTML index and other static files
    export_skeleton(
        static_folder=static_folder,
        dev_mode=False,
        languages=languages,
        formats=formats,
        only_books=only_books,
        title_search=title_search,
        add_bookshelves=add_bookshelves,
    )

    # Compute popularity
    popbooks = books.order_by(Book.downloads.desc())
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

    for book in books:
        book.popularity = sum(
            [int(book.downloads >= stars_limits[i]) for i in range(NB_POPULARITY_STARS)]
        )

    def dlb(b):
        return export_book(
            b,
            static_folder=pathlib.Path(static_folder),
            book_dir=pathlib.Path(download_cache).joinpath(str(b.id)),
            languages=languages,
            formats=formats,
            books=books,
            project_id=project_id,
            force=force,
            title_search=title_search,
            add_bookshelves=add_bookshelves,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version,
        )

    Pool(concurrency).map(dlb, books)


def html_content_for(book, src_dir):

    html_fpath = src_dir.joinpath(fname_for(book, "html"))

    # is HTML file present?
    if not html_fpath.exists():
        logger.warn("Missing HTML content for #{} at {}".format(book.id, html_fpath))
        return None, None

    try:
        return read_file(html_fpath)
    except UnicodeDecodeError:
        logger.error("Unable to read HTML content: {}".format(html_fpath))
        raise


def update_html_for_static(book, html_content, epub=False):
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
            except Exception:
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
                    "images/", "{id}_".format(id=book.id)
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
            nurl = "{id}_{url}".format(id=book.id, url=urlp)
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
                soup.html.insert(0, head)
            head.append(soup.new_tag("title"))
            soup.title.string = book.title

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
            "<><><><><><><><><><><><><><><><><><><><><><><><><><><><>" "<><><><><><>",
            "<><><><><><><><><><><><><><><><><><><><><><><><><><><><>" "<><><><><><>",
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
        ("—————————————————-", "Encode an ISO 8859/1 " "Etext into LaTeX or HTML"),
    ]

    body = soup.find("body")
    try:
        is_encapsulated_in_div = (
            sum([1 for e in body.children if not isinstance(e, bs4.NavigableString)])
            == 1
        )
    except Exception:
        is_encapsulated_in_div = False

    if is_encapsulated_in_div and not epub:
        DEBUG_COUNT.append((book.id, book.title))

    if not is_encapsulated_in_div:
        for start_of_text, end_of_text in patterns:
            if start_of_text not in body.text and end_of_text not in body.text:
                continue

            if start_of_text in body.text and end_of_text in body.text:
                remove = True
                for child in body.children:
                    if isinstance(child, bs4.NavigableString):
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
                # logger.debug("FOUND START: {}".format(start_of_text))
                remove = True
                for child in body.children:
                    if isinstance(child, bs4.NavigableString):
                        continue
                    if start_of_text in getattr(child, "text", ""):
                        child.decompose()
                        remove = False
                    if remove:
                        child.decompose()
                break
            elif end_of_text in body.text:
                # logger.debug("FOUND END: {}".format(end_of_text))
                remove = False
                for child in body.children:
                    if isinstance(child, bs4.NavigableString):
                        continue
                    if end_of_text in getattr(child, "text", ""):
                        remove = True
                    if remove:
                        child.decompose()
                break

    # build infobox
    if not epub:
        infobox = jinja_env.get_template("book_infobox.html")
        infobox_html = infobox.render({"book": book})
        info_soup = BeautifulSoup(infobox_html, "lxml-html")
        body.insert(0, info_soup.find("div"))

    # if there is no charset, set it to utf8
    if not epub:
        meta = BeautifulSoup(
            '<meta http-equiv="Content-Type" ' 'content="text/html; charset=UTF-8" />',
            "lxml-html",
        )
        head = soup.find("head")
        html = soup.find("html")
        if head:
            head.insert(0, meta.head.contents[0])
        elif html:
            html.insert(0, meta.head)
        else:
            soup.insert(0, meta.head)

        return html

    return soup


def cover_html_content_for(
    book, static_folder, books, project_id, title_search, add_bookshelves
):
    cover_img = "{id}_cover_image.jpg".format(id=book.id)
    cover_img = cover_img if static_folder.joinpath(cover_img).exists() else None
    translate_author = (
        ' data-l10n-id="author-{id}"'.format(id=book.author.name().lower())
        if book.author.name() in ["Anonymous", "Various"]
        else ""
    )
    translate_license = (
        ' data-l10n-id="license-{id}"'.format(id=book.license.slug.lower())
        if book.license.slug in ["PD", "Copyright"]
        else ""
    )
    context = get_default_context(project_id=project_id, books=books)
    context.update(
        {
            "book": book,
            "cover_img": cover_img,
            "formats": main_formats_for(book),
            "translate_author": translate_author,
            "translate_license": translate_license,
            "title_search": title_search,
            "add_bookshelves": add_bookshelves,
        }
    )
    template = jinja_env.get_template("cover_article.html")
    return template.render(**context)


def author_html_content_for(author, books, project_id):
    context = get_default_context(project_id=project_id, books=books)
    context.update({"author": author})
    template = jinja_env.get_template("author.html")
    return template.render(**context)


def save_author_file(author, static_folder, books, project_id, force=False):
    fpath = os.path.join(static_folder, "{}.html".format(author.fname()))
    if path(fpath).exists() and not force:
        logger.debug("\t\tSkipping author file {}".format(fpath))
        return
    logger.debug("\t\tSaving author file {}".format(fpath))
    save_file(author_html_content_for(author, books, project_id), fpath, UTF8)


def export_book(
    book,
    static_folder,
    book_dir,
    languages,
    formats,
    books,
    project_id,
    force,
    title_search,
    add_bookshelves,
    s3_storage,
    optimizer_version,
):
    optimized_files_dir = book_dir.joinpath("optimized")
    if optimized_files_dir.exists():
        for fpath in optimized_files_dir.iterdir():
            if not static_folder.joinpath(fpath.name).exists():
                shutil.copy2(fpath, static_folder)
    unoptimized_files_dir = book_dir.joinpath("unoptimized")
    if unoptimized_files_dir.exists():
        handle_unoptimized_files(
            book=book,
            static_folder=static_folder,
            src_dir=unoptimized_files_dir,
            languages=languages,
            formats=formats,
            books=books,
            project_id=project_id,
            force=force,
            title_search=title_search,
            add_bookshelves=add_bookshelves,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version,
        )

    write_book_presentation_article(
        static_folder=static_folder,
        book=book,
        force=force,
        project_id=project_id,
        title_search=title_search,
        add_bookshelves=add_bookshelves,
        books=books,
    )


def handle_unoptimized_files(
    book,
    static_folder,
    src_dir,
    languages,
    formats,
    books,
    project_id,
    optimizer_version,
    force=False,
    title_search=False,
    add_bookshelves=False,
    s3_storage=None,
):
    def copy_file(src, dst):
        logger.info("\t\tCopying {}".format(dst))
        try:
            shutil.copy2(src, dst)
        except IOError:
            logger.error("/!\\ Unable to copy missing file {}".format(src))
            return

    def update_download_cache(unoptimized_file, optimized_file):
        book_dir = unoptimized_file.parents[1]
        optimized_dir = book_dir.joinpath("optimized")
        unoptimized_dir = book_dir.joinpath("unoptimized")
        if not optimized_dir.exists():
            optimized_dir.mkdir()
        dst = optimized_dir.joinpath(optimized_file.name)
        os.unlink(unoptimized_file)
        copy_file(optimized_file.resolve(), dst.resolve())
        if not [fpath for fpath in unoptimized_dir.iterdir()]:
            unoptimized_dir.rmdir()

    logger.info("\tExporting Book #{id}.".format(id=book.id))

    # actual book content, as HTML
    html, _ = html_content_for(book=book, src_dir=src_dir)
    html_book_optimized_files = []
    if html:
        article_fpath = static_folder.joinpath(article_name_for(book))
        if not article_fpath.exists() or force:
            logger.info("\t\tExporting to {}".format(article_fpath))
            try:
                new_html = update_html_for_static(book=book, html_content=html)
            except Exception:
                raise
            save_bs_output(new_html, article_fpath, UTF8)
            html_book_optimized_files.append(article_fpath)
            update_download_cache(
                src_dir.joinpath(fname_for(book, "html")), article_fpath
            )
            if not src_dir.exists():
                return
        else:
            logger.info("\t\tSkipping HTML article {}".format(article_fpath))

    def optimize_image(src, dst, force=False):
        if dst.exists() and not force:
            logger.info("\tSkipping image optimization for {}".format(dst))
            return dst
        logger.info("\tOptimizing image {}".format(dst))
        if src.suffix == ".png":
            return optimize_png(str(src.resolve()), str(dst.resolve()))
        if src.suffix in (".jpg", ".jpeg"):
            return optimize_jpeg(str(src.resolve()), str(dst.resolve()))
        if src.suffix == ".gif":
            return optimize_gif(str(src.resolve()), str(dst.resolve()))
        return dst

    def optimize_gif(src, dst):
        exec_cmd(["gifsicle", "-O3", src, "-o", dst])

    def optimize_png(src, dst):
        exec_cmd(["pngquant", "--nofs", "--force", "--output", dst, src])
        exec_cmd(["advdef", "-z", "-4", "-i", "5", dst])

    def optimize_jpeg(src, dst):
        if src != dst:
            copy_file(src, dst)
        exec_cmd(["jpegoptim", "--strip-all", "-m50", dst])

    def optimize_epub(src, dst):
        logger.info("\t\tCreating ePUB off {} at {}".format(src, dst))
        zipped_files = []
        # create temp directory to extract to
        tmpd = tempfile.mkdtemp(dir=TMP_FOLDER)

        try:
            with zipfile.ZipFile(src, "r") as zf:
                zipped_files = zf.namelist()
                zf.extractall(tmpd)
        except zipfile.BadZipFile as exc:
            shutil.rmtree(tmpd)
            raise exc

        remove_cover = False
        for fname in zipped_files:
            fnp = os.path.join(tmpd, fname)
            if path(fname).ext in (".png", ".jpeg", ".jpg", ".gif"):

                # special case to remove ugly cover
                if fname.endswith("cover.jpg") and is_bad_cover(fnp):
                    zipped_files.remove(fname)
                    remove_cover = True
                else:
                    optimize_image(pathlib.Path(fnp), pathlib.Path(fnp), force=True)

            if path(fname).ext in (".htm", ".html"):
                html_content, _ = read_file(fnp)
                html = update_html_for_static(
                    book=book, html_content=html_content, epub=True
                )
                save_bs_output(html, fnp, UTF8)

            if path(fname).ext == ".ncx":
                pattern = "*** START: FULL LICENSE ***"
                ncx, _ = read_file(fnp)
                soup = BeautifulSoup(ncx, "lxml-xml")
                for tag in soup.findAll("text"):
                    if pattern in tag.text:
                        s = tag.parent.parent
                        s.decompose()
                        for s in s.next_siblings:
                            s.decompose()
                        s.next_sibling

                save_bs_output(soup, fnp, UTF8)

        # delete {id}/cover.jpg if exist and update {id}/content.opf
        if remove_cover:

            # remove cover
            path(os.path.join(tmpd, text_type(book.id), "cover.jpg")).unlink_p()

            soup = None
            opff = os.path.join(tmpd, text_type(book.id), "content.opf")
            if os.path.exists(opff):
                opff_content, _ = read_file(opff)
                soup = BeautifulSoup(opff_content, "lxml-xml")

                for elem in soup.findAll():
                    if getattr(elem, "attrs", {}).get("href") == "cover.jpg":
                        elem.decompose()

                save_bs_output(soup, opff, UTF8)

        # bundle epub as zip
        zip_epub(epub_fpath=dst, root_folder=tmpd, fpaths=zipped_files)

        path(tmpd).rmtree_p()

    def handle_companion_file(
        fname,
        dstfname=None,
        book=None,
        force=False,
        as_ext=None,
        html_file_list=None,
        s3_storage=None,
    ):
        ext = fname.suffix if as_ext is None else as_ext
        src = fname
        if dstfname is None:
            dstfname = fname.name
        dst = static_folder.joinpath(dstfname)
        if dst.exists() and not force:
            logger.debug("\t\tSkipping existing companion {}".format(dstfname))
            return

        # optimization based on mime/extension
        if ext in (".png", ".jpg", ".jpeg", ".gif"):
            logger.info("\t\tCopying and optimizing image companion {}".format(fname))
            optimize_image(src, dst)
            if dst.name == (f"{book.id}_cover_image.jpg"):
                if s3_storage:
                    upload_to_cache(
                        asset=dst,
                        book_format="cover",
                        book_id=book.id,
                        etag=book.cover_etag,
                        s3_storage=s3_storage,
                        optimizer_version=optimizer_version,
                    )
                update_download_cache(src, dst)
            elif html_file_list:
                html_file_list.append(dst)
                update_download_cache(src, dst)
        elif ext == ".epub":
            logger.info("\t\tCreating optimized EPUB file {}".format(fname))
            tmp_epub = tempfile.NamedTemporaryFile(suffix=".epub", dir=TMP_FOLDER)
            tmp_epub.close()
            try:
                optimize_epub(src, tmp_epub.name)
            except zipfile.BadZipFile:
                logger.warn(
                    "\t\tBad zip file. "
                    "Copying as it might be working{}".format(fname)
                )
                handle_companion_file(fname, dstfname, book, force, as_ext=".zip")
            else:
                path(tmp_epub.name).move(dst)
                if s3_storage:
                    upload_to_cache(
                        asset=dst,
                        book_format="epub",
                        book_id=book.id,
                        etag=book.epub_etag,
                        s3_storage=s3_storage,
                        optimizer_version=optimizer_version,
                    )
                update_download_cache(src, dst)
        else:
            # excludes files created by Windows Explorer
            if src.name.endswith("_Thumbs.db"):
                return
            # copy otherwise (PDF mostly)
            logger.info("\t\tCopying companion file to {}".format(dst))
            copy_file(src, dst)
            if ext != ".pdf" and ext != ".zip" and html_file_list:
                html_file_list.append(dst)
                update_download_cache(src, dst)

    # associated files (images, etc)
    for fpath in src_dir.iterdir():
        if fpath.is_file() and fpath.name.startswith(f"{book.id}_"):
            if fpath.suffix in (".html", ".htm"):
                src = fpath
                dst = static_folder.joinpath(fpath.name)
                if dst.exists() and not force:
                    logger.debug("\t\tSkipping existing HTML {}".format(dst))
                    continue

                logger.info("\t\tExporting HTML file to {}".format(dst))
                html, _ = read_file(src)
                new_html = update_html_for_static(book=book, html_content=html)
                save_bs_output(new_html, dst, UTF8)
                html_book_optimized_files.append(dst)
                update_download_cache(src, dst)
            else:
                try:
                    handle_companion_file(
                        fpath,
                        force=force,
                        html_file_list=html_book_optimized_files,
                        s3_storage=s3_storage,
                        book=book,
                    )
                except Exception as e:
                    logger.exception(e)
                    logger.error(
                        "\t\tException while handling companion file: {}".format(e)
                    )
    if s3_storage and html_book_optimized_files:
        upload_to_cache(
            asset=html_book_optimized_files,
            book_format="html",
            etag=book.html_etag,
            book_id=book.id,
            s3_storage=s3_storage,
            optimizer_version=optimizer_version,
        )

    # other formats
    for format in formats:
        if format not in book.formats() or format == "html":
            continue
        book_file = src_dir.joinpath(fname_for(book, format))
        if book_file.exists():
            try:
                handle_companion_file(
                    book_file,
                    archive_name_for(book, format),
                    force=force,
                    book=book,
                    s3_storage=s3_storage,
                )
            except Exception as e:
                logger.exception(e)
                logger.error(
                    "\t\tException while handling companion file: {}".format(e)
                )


def write_book_presentation_article(
    static_folder, book, force, project_id, title_search, add_bookshelves, books
):
    cover_fpath = static_folder.joinpath(article_name_for(book=book, cover=True))
    if not cover_fpath.exists() or force:
        logger.info("\t\tExporting to {}".format(cover_fpath))
        html = cover_html_content_for(
            book=book,
            static_folder=static_folder,
            books=books,
            project_id=project_id,
            title_search=title_search,
            add_bookshelves=add_bookshelves,
        )
        with open(cover_fpath, "w") as f:
            if six.PY2:
                f.write(html.encode(UTF8))
            else:
                f.write(html)
    else:
        logger.info("\t\tSkipping cover {}".format(cover_fpath))


def authors_from_ids(idlist):
    """build a list of Author objects based on a list of author.gut_id

    Used to overcome large SELECT IN SQL stmts which peewee complains
    about. Slower !!"""
    authors = []
    for author in Author.select().order_by(
        Author.last_name.asc(), Author.first_names.asc()
    ):
        if author.gut_id not in idlist:
            continue
        if author in authors:
            continue
        authors.append(author)
    return authors


# Returns the list of all Bookshelves
# Ex: [None, u'Adventure', u"Children's Literature", u'Christianity',
# u'Detective Fiction', u'Gothic Fiction', u'Harvard Classics', u'Historical Fiction',
# u'Mathematics', u'Plays', u'School Stories', u'Science Fiction']
def bookshelf_list(books):
    return [
        bookshelf.bookshelf
        for bookshelf in books.select()
        .order_by(Book.bookshelf.asc())
        .group_by(Book.bookshelf)
    ]


def bookshelf_list_language(books, lang):
    return [
        bookshelf.bookshelf
        for bookshelf in books.select()
        .where(Book.language == lang)
        .order_by(Book.bookshelf.asc())
        .group_by(Book.bookshelf)
    ]


def export_to_json_helpers(
    books, static_folder, languages, formats, project_id, title_search, add_bookshelves
):
    def dumpjs(col, fn, var="json_data"):
        with open(os.path.join(static_folder, fn), "w") as f:
            f.write("var {var} = ".format(var=var))
            f.write(json.dumps(col))
            f.write(";")
            # json.dump(col, f)

    # all books sorted by popularity
    logger.info("\t\tDumping full_by_popularity.js")
    dumpjs(
        [book.to_array() for book in books.order_by(Book.downloads.desc())],
        "full_by_popularity.js",
    )

    # all books sorted by title
    logger.info("\t\tDumping full_by_title.js")
    dumpjs(
        [book.to_array() for book in books.order_by(Book.title.asc())],
        "full_by_title.js",
    )

    avail_langs = get_langs_with_count(books=books)

    all_filtered_authors = []

    # language-specific collections
    for lang_name, lang, lang_count in avail_langs:
        lang_filtered_authors = list(
            set([book.author.gut_id for book in books.filter(language=lang)])
        )
        for aid in lang_filtered_authors:
            if aid not in all_filtered_authors:
                all_filtered_authors.append(aid)

        # by popularity
        logger.info("\t\tDumping lang_{}_by_popularity.js".format(lang))
        dumpjs(
            [
                book.to_array()
                for book in books.where(Book.language == lang).order_by(
                    Book.downloads.desc()
                )
            ],
            "lang_{}_by_popularity.js".format(lang),
        )
        # by title
        logger.info("\t\tDumping lang_{}_by_title.js".format(lang))
        dumpjs(
            [
                book.to_array()
                for book in books.where(Book.language == lang).order_by(
                    Book.title.asc()
                )
            ],
            "lang_{}_by_title.js".format(lang),
        )

        authors = authors_from_ids(lang_filtered_authors)
        logger.info("\t\tDumping authors_lang_{}.js".format(lang))
        dumpjs(
            [author.to_array() for author in authors],
            "authors_lang_{}.js".format(lang),
            "authors_json_data",
        )

    if add_bookshelves:
        bookshelves = bookshelf_list(books)
        for bookshelf in bookshelves:
            # exclude the books with no bookshelf data
            if bookshelf is None:
                continue
            # dumpjs for bookshelf by popularity
            # this will allow the popularity button to use this js on the
            # particular bookshelf page
            logger.info("\t\tDumping bookshelf_{}_by_popularity.js".format(bookshelf))
            dumpjs(
                [
                    book.to_array()
                    for book in books.select()
                    .where(Book.bookshelf == bookshelf)
                    .order_by(Book.downloads.desc())
                ],
                "bookshelf_{}_by_popularity.js".format(bookshelf),
            )

            # by title
            logger.info("\t\tDumping bookshelf_{}_by_title.js".format(bookshelf))
            dumpjs(
                [
                    book.to_array()
                    for book in books.select()
                    .where(Book.bookshelf == bookshelf)
                    .order_by(Book.title.asc())
                ],
                "bookshelf_{}_by_title.js".format(bookshelf),
            )
            # by language
            for lang_name, lang, lang_count in avail_langs:
                logger.info(
                    "\t\tDumping bookshelf_{}_by_lang_{}.js".format(bookshelf, lang)
                )
                dumpjs(
                    [
                        book.to_array()
                        for book in books.select()
                        .where(Book.language == lang)
                        .where(Book.bookshelf == bookshelf)
                        .order_by(Book.downloads.desc())
                    ],
                    "bookshelf_{}_lang_{}_by_popularity.js".format(bookshelf, lang),
                )

                dumpjs(
                    [
                        book.to_array()
                        for book in books.select()
                        .where(Book.language == lang)
                        .where(Book.bookshelf == bookshelf)
                        .order_by(Book.title.asc())
                    ],
                    "bookshelf_{}_lang_{}_by_title.js".format(bookshelf, lang),
                )

        # dump all bookshelves from any given language
        for lang_name, lang, lang_count in avail_langs:
            logger.info("\t\tDumping bookshelves_lang_{}.js".format(lang))
            temp = bookshelf_list_language(books, lang)
            dumpjs(temp, "bookshelves_lang_{}.js".format(lang))

        logger.info("\t\tDumping bookshelves.js")
        dumpjs(bookshelves, "bookshelves.js", "bookshelves_json_data")

        # Create the bookshelf home page
        context = get_default_context(project_id=project_id, books=books)
        context.update({"bookshelf_home": True, "add_bookshelves": True})
        template = jinja_env.get_template("bookshelf_home.html")
        rendered = template.render(**context)
        save_bs_output(
            rendered, os.path.join(static_folder, "bookshelf_home.html"), UTF8
        )

        # add individual bookshelf pages
        for bookshelf in bookshelves:
            if bookshelf is None:
                continue
            context["bookshelf"] = bookshelf
            context.update(
                {
                    "bookshelf_home": False,
                    "individual_book_shelf": True,
                    "no_filters": True,
                    "add_bookshelves": True,
                }
            )
            template = jinja_env.get_template("bookshelf.html")
            rendered = template.render(**context)
            savepath = os.path.join(static_folder, "{}.html".format(bookshelf))
            # logger.info("Saving {} to {}".format(bookshelf, savepath))
            save_bs_output(rendered, savepath, UTF8)

    # author specific collections
    authors = authors_from_ids(all_filtered_authors)
    for author in authors:

        # all_filtered_authors.remove(author.gut_id)
        # by popularity
        logger.info("\t\tDumping auth_{}_by_popularity.js".format(author.gut_id))
        dumpjs(
            [
                book.to_array()
                for book in books.where(Book.author == author).order_by(
                    Book.downloads.desc()
                )
            ],
            "auth_{}_by_popularity.js".format(author.gut_id),
        )
        # by title
        logger.info("\t\tDumping auth_{}_by_title.js".format(author.gut_id))
        dumpjs(
            [
                book.to_array()
                for book in books.where(Book.author == author).order_by(
                    Book.title.asc()
                )
            ],
            "auth_{}_by_title.js".format(author.gut_id),
        )
        # by language
        for lang_name, lang, lang_count in avail_langs:
            logger.info("\t\tDumping auth_{}_by_lang_{}.js".format(author.gut_id, lang))
            dumpjs(
                [
                    book.to_array()
                    for book in books.where(Book.language == lang)
                    .where(Book.author == author)
                    .order_by(Book.downloads.desc())
                ],
                "auth_{}_lang_{}_by_popularity.js".format(author.gut_id, lang),
            )

            dumpjs(
                [
                    book.to_array()
                    for book in books.where(Book.language == lang)
                    .where(Book.author == author)
                    .order_by(Book.title.asc())
                ],
                "auth_{}_lang_{}_by_title.js".format(author.gut_id, lang),
            )

        # author HTML redirect file
        save_author_file(author, static_folder, books, project_id, force=True)

    # authors list sorted by name
    logger.info("\t\tDumping authors.js")
    dumpjs([author.to_array() for author in authors], "authors.js", "authors_json_data")

    # languages list sorted by code
    logger.info("\t\tDumping languages.js")
    dumpjs(avail_langs, "languages.js", "languages_json_data")

    # languages by weight
    main_languages, other_languages = get_lang_groups(books)
    logger.info("\t\tDumping main_languages.js")
    dumpjs(main_languages, "main_languages.js", "main_languages_json_data")
    dumpjs(other_languages, "other_languages.js", "other_languages_json_data")
