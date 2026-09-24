"""Wikisource format resolution.

Every OPDS entry already advertises its download links (one ws-export URL per
format), which `sources.wikisource.metadata` stores on `Work.formats`. Resolving
a format is therefore a lookup on the work, not a URL translation.
"""

from gutenberg2zim.core.models import Work
from gutenberg2zim.core.ports import DownloadRequest, FormatResolverPort


class WikisourceFormatResolver(FormatResolverPort):
    """`FormatResolverPort` reading the ws-export links parsed from the feed."""

    def resolve(self, work: Work, format_name: str) -> DownloadRequest | None:
        url = next(
            (fmt.url for fmt in work.formats if fmt.name == format_name and fmt.url),
            None,
        )
        if url is None:
            return None
        return DownloadRequest(url=url, format_name=format_name)
