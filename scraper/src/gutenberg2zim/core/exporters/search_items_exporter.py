"""Search items exporter: writes the ZIM full-text/title index entries.

These are not JSON files but tiny HTML redirect pages (`index/<fname>`)
pointing at Vue.js UI routes, wrapped with `IndexData` so the ZIM search
index picks them up. The entries themselves are derived once by
`core.index_builder.IndexBuilder`; this module only owns the on-ZIM
encoding and writing.
"""

from html import escape

from zimscraperlib.zim.indexing import IndexData

from gutenberg2zim.constants import logger
from gutenberg2zim.core.index_builder import Indexes
from gutenberg2zim.core.zim_assembler import ZimAssembler


def add_search_item(
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


def export_search_items(indexes: Indexes, assembler: ZimAssembler) -> None:
    """Write all search index entries (books, authors, shelves, listings)"""
    logger.debug("Generating ZIM index entries")
    for entry in indexes.search_entries:
        add_search_item(
            title=entry.title,
            content=entry.content,
            fname=entry.fname,
            vue_route=entry.route,
            assembler=assembler,
        )
