"""Open Textbook Library format resolution.

Unlike Gutenberg (deterministic mirror URLs), OTL embeds download links in
each textbook record; `sources.opentextbooks.metadata` stores them on
`Work.formats`, so resolution is a lookup, not a URL translation.

Caveat: most OTL "PDF"/"eBook" links point at landing pages (publisher or
author sites), not actual files. Only direct file links (URL path ending in
`.pdf` / `.epub`) are resolved; books whose links are all landing pages end
up with no downloadable format and follow the existing drop-book behavior.
External hosts and occasional link rot are handled by the `DownloadEngine`.
"""

from urllib.parse import urlparse

from gutenberg2zim.core.models import Work
from gutenberg2zim.core.ports import DownloadRequest, FormatResolverPort

# CLI format name -> (OTL format type, expected file extension)
FORMAT_TYPES = {
    "pdf": ("PDF", ".pdf"),
    "epub": ("eBook", ".epub"),
    "html": ("Online", None),
}


def is_direct_file_url(url: str, extension: str) -> bool:
    """Return whether a URL path is a direct file of the expected type."""
    return urlparse(url).path.lower().endswith(extension)


class OpenTextbookLibraryFormatResolver(FormatResolverPort):
    """`FormatResolverPort` implementation reading OTL record download links"""

    def resolve(self, work: Work, format_name: str) -> DownloadRequest | None:
        wanted = FORMAT_TYPES.get(format_name)
        if not wanted:
            return None
        otl_type, extension = wanted
        candidate_urls = [
            fmt.url
            for fmt in work.formats
            if fmt.name == otl_type
            and fmt.url
            and (extension is None or is_direct_file_url(fmt.url, extension))
        ]
        if not candidate_urls:
            return None
        return DownloadRequest(
            url=candidate_urls[0],
            format_name=format_name,
            extra={"candidate_urls": candidate_urls},
        )
