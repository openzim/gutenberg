"""Generic relative link rewriting (moved from the Gutenberg rewriting module).

Rewrites relative links to sibling HTML pages into `{item_id}_{page}` form
so they resolve inside the ZIM. Source-agnostic: takes a plain item id.
"""


def replacement_link(item_id: str, url: str) -> str | None:
    try:
        urlp, anchor = url.rsplit("#", 1)
    except ValueError:
        urlp = url
        anchor = None
    if "/" in urlp:
        return None

    if len(urlp.strip()):
        nurl = f"{item_id}_{urlp}"
    else:
        nurl = ""

    if anchor is not None:
        return "#".join([nurl, anchor])

    return nurl
