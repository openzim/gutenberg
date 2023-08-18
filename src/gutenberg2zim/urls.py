import os
import urllib.parse as urlparse
from collections import defaultdict

from path import Path

from gutenberg2zim.constants import logger
from gutenberg2zim.database import Book, BookFormat, Url
from gutenberg2zim.utils import FORMAT_MATRIX, exec_cmd


class UrlBuilder:

    """
    Url builder for the files of a Gutenberg book.
    Example:
        >>> builder = UrlBuilder()
        >>> builder.with_id(<some_id>)
        >>> builder.with_base(UrlBuilder.BASE_{ONE|TWO|THREE})
        >>> url = builder.build()
    """

    SERVER_NAME = "aleph_pglaf_org"
    RSYNC = "rsync://aleph.pglaf.org/gutenberg/"
    BASE_ONE = "http://aleph.pglaf.org/"
    BASE_TWO = "http://aleph.pglaf.org/cache/epub/"
    BASE_THREE = "http://aleph.pglaf.org/etext"

    def __init__(self):
        self.base = self.BASE_ONE

    def build(self):
        """
        Build either an url depending on whether the base url
        is `BASE_ONE` or `BASE_TWO`.
        The former generates urls according to the Url pattern:
            id: 10023 -> pattern: <base-url>/1/0/0/2/10023
        The latter generates urls according to the Url pattern:
            id: 10023 -> pattern: <base-url>/10023
        There's no implementation for the book Id's 0-10, because
        these books do not exist.

        """
        if self.base == self.BASE_ONE:
            if int(self.b_id) > 10:  # noqa: PLR2004
                base_url = os.path.join(
                    os.path.join(*list(str(self.b_id))[:-1]), str(self.b_id)
                )
            else:
                base_url = os.path.join(os.path.join("0", str(self.b_id)))
            url = os.path.join(self.base, base_url)
        elif self.base == self.BASE_TWO:
            url = os.path.join(self.base, str(self.b_id))
        elif self.base == self.BASE_THREE:
            url = self.base
        return url  # type: ignore

    def with_base(self, base):
        self.base = base

    def with_id(self, b_id):
        self.b_id = b_id

    def __unicode__(self):
        return self.build_url()  # type: ignore


def get_urls(book):
    """
    Get all possible urls that could point to the
    book on either of the two mirrors.
    param: book: The book you want the possible urls from
    returns: a list of all possible urls sorted by their probability
    """
    filtered_book = BookFormat.select().where(BookFormat.book == book)

    # Strip out the encoding of the file
    def f(x):
        return x.mime.split(";")[0].strip()

    available_formats = [
        {x.pattern.format(id=book.id): {"mime": f(x), "id": book.id}}
        for x in filtered_book
        if f(x) in FORMAT_MATRIX.values()
    ]
    files = sort_by_mime_type(available_formats)
    return build_urls(files)


def sort_by_mime_type(files):
    """
    Reverse the passed in `files` dict and return a dict
    that is sorted by `{mimetype: {filetype, id}}` instead of
    by `{filetype: mimetype}`.
    """
    mime = defaultdict(list)
    for f in files:
        for k, v in f.items():
            mime[v["mime"]].append({"name": k, "id": v["id"]})
    return dict(mime)


def build_urls(files):
    mapping = {
        "application/epub+zip": build_epub,
        "application/pdf": build_pdf,
        "text/html": build_html,
    }

    for i in mapping:
        if i in files:
            possible_url = mapping[i](files[i])
            filtre = [
                u
                for u in possible_url
                if Url.get_or_none(url=urlparse.urlparse(u).path[1:])
            ]
            # Use only the URLs in DB
            files[i] = filtre
            # for development
            # if len(filtre) == 0 and len(possible_url) != 0:
            #     files[i] = possible_url
            # else:
            #     files[i] = filtre

    return files


def index_of_substring(lst, substrings):
    for i, s in enumerate(lst):
        for substring in substrings:
            if substring in s:
                return i
    return -1


def build_epub(files):
    """
    Build the posssible urls of the epub file.
    """
    urls = []
    b_id = str(files[0]["id"])
    u = UrlBuilder()
    u.with_id(b_id)
    u.with_base(UrlBuilder.BASE_TWO)

    if not u.build():
        return []

    name = "".join(["pg", b_id])
    url = os.path.join(u.build(), name + ".epub")
    url_images = os.path.join(u.build(), name + "-images.epub")
    url_noimages = os.path.join(u.build(), name + "-noimages.epub")
    urls.extend([url, url_images, url_noimages])
    return urls


def build_pdf(files):
    """
    Build the posssible urls of the pdf files.
    """
    urls = []
    b_id = str(files[0]["id"])
    u = UrlBuilder()
    u.with_base(UrlBuilder.BASE_TWO)
    u.with_id(b_id)

    u1 = UrlBuilder()
    u1.with_base(UrlBuilder.BASE_ONE)
    u1.with_id(b_id)

    if not u.build():
        return []

    for i in files:
        if "images" not in i["name"]:
            url = os.path.join(u.build(), i["name"])
            urls.append(url)

    url_dash1 = os.path.join(u1.build(), b_id + "-" + "pdf" + ".pdf")
    url_dash = os.path.join(u.build(), b_id + "-" + "pdf" + ".pdf")
    url_normal = os.path.join(u.build(), b_id + ".pdf")
    url_pg = os.path.join(u.build(), "pg" + b_id + ".pdf")

    urls.extend([url_dash, url_normal, url_pg, url_dash1])
    return list(set(urls))


def build_html(files):
    """
    Build the posssible urls of the html files.
    """
    urls = []
    b_id = str(files[0]["id"])
    file_names = [i["name"] for i in files]
    u = UrlBuilder()
    u.with_id(b_id)

    if not u.build():
        return []

    if all(["-h.html" not in file_names, "-h.zip" in file_names]):
        for i in files:
            url = os.path.join(u.build(), i["name"])
            urls.append(url)

    url_zip = os.path.join(u.build(), b_id + "-h" + ".zip")
    # url_utf8 = os.path.join(u.build(), b_id + '-8' + '.zip')
    url_html = os.path.join(u.build(), b_id + "-h" + ".html")
    url_htm = os.path.join(u.build(), b_id + "-h" + ".htm")

    u.with_base(UrlBuilder.BASE_TWO)
    name = "".join(["pg", b_id])
    html_utf8 = os.path.join(u.build(), name + ".html.utf8")

    u.with_base(UrlBuilder.BASE_THREE)
    file_index = index_of_substring(files, ["html", "htm"])
    file_name = files[file_index]["name"]
    etext_nums = []
    etext_nums.extend(range(90, 100))
    etext_nums.extend(range(0, 6))
    etext_names = [f"{i:0=2d}" for i in etext_nums]
    etext_urls = []
    for i in etext_names:
        etext_urls.append(os.path.join(u.build() + i, file_name))

    urls.extend([url_zip, url_htm, url_html, html_utf8])
    urls.extend(etext_urls)
    return list(set(urls))


def setup_urls(force):
    file_with_url = os.path.join("tmp", f"file_on_{UrlBuilder.SERVER_NAME}")

    if Path(file_with_url).exists() and not force:
        logger.info(
            "\tUrls rsync result {} already exists, processing existing file".format(
                file_with_url
            )
        )
    else:
        cmd = [
            "bash",
            "-c",
            f"rsync -a --list-only {UrlBuilder.RSYNC} > {file_with_url}",
        ]
        exec_cmd(cmd)

    logger.info("\tLooking after relative path start in urls rsync result")
    # search for "GUTINDEX*" file, so that we known where starts the relative
    # path in rsync output
    with open(file_with_url, errors="replace") as src:
        for line in src.readlines():
            start_rel_path_idx = line.find("GUTINDEX")
            if start_rel_path_idx >= 0:
                break

    if start_rel_path_idx == -1:  # type: ignore
        raise ValueError("Unable to find relative path start in urls file")

    logger.info("\tRemoving all urls already present in DB")
    qry = Url.delete()
    qry.execute()

    logger.info("\tAppending urls in DB from rsync result")
    # strip rsync file to only contain relative path
    with open(file_with_url, errors="replace") as src:
        for line in src.readlines():
            Url.create(url=line[start_rel_path_idx:].strip())  # type: ignore


if __name__ == "__main__":
    book = Book.get(id=9)
    print(get_urls(book))  # noqa: T201
