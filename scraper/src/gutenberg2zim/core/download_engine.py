"""Generic HTTP download engine.

Source-agnostic downloader with a persistent session, retry with backoff,
an on-disk cache keyed by URL hash, and streaming to file. Sources hand it
`DownloadRequest`s (from their `FormatResolverPort`); it knows nothing
about any specific source's URL scheme.
"""

import hashlib
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import backoff
import requests

from gutenberg2zim.constants import DEFAULT_HTTP_TIMEOUT, DL_CHUNCK_SIZE, logger
from gutenberg2zim.core.ports import DownloadRequest


@dataclass(frozen=True, slots=True)
class DownloadResult:
    url: str
    path: Path
    size: int
    from_cache: bool


def _is_fatal_http_error(exc: Exception) -> bool:
    """Give up on error codes 400-499 except 429"""
    return (
        isinstance(exc, requests.HTTPError)
        and exc.response is not None
        and HTTPStatus.BAD_REQUEST
        <= exc.response.status_code
        < HTTPStatus.INTERNAL_SERVER_ERROR
        and exc.response.status_code != HTTPStatus.TOO_MANY_REQUESTS
    )


class DownloadEngine:
    def __init__(
        self,
        cache_dir: Path,
        session: requests.Session | None = None,
        timeout: int = DEFAULT_HTTP_TIMEOUT,
        max_retry_time: int = 30,
    ):
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = session or requests.Session()
        self._timeout = timeout
        self._max_retry_time = max_retry_time

    def cache_path_for(self, url: str) -> Path:
        """Deterministic cache path for a URL (hash + original suffix)"""
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        suffix = Path(urlparse(url).path).suffix
        return self._cache_dir / f"{digest}{suffix}"

    def download(
        self, request: DownloadRequest, dest: Path | None = None
    ) -> DownloadResult:
        """Download `request.url` to `dest` (or request.target, or the cache).

        Returns the cached file directly when the URL was downloaded before
        and no explicit destination is requested.
        """
        target = dest or request.target
        cache_path = self.cache_path_for(request.url)

        if target is None and cache_path.exists():
            logger.debug(f"\t\tCache hit for {request.url}")
            return DownloadResult(
                url=request.url,
                path=cache_path,
                size=cache_path.stat().st_size,
                from_cache=True,
            )

        target = target or cache_path
        self._download_with_retry(request.url, target)
        return DownloadResult(
            url=request.url,
            path=target,
            size=target.stat().st_size,
            from_cache=False,
        )

    def _download_with_retry(self, url: str, target: Path) -> None:
        @backoff.on_exception(
            backoff.expo,
            requests.exceptions.RequestException,
            max_time=self._max_retry_time,
            giveup=_is_fatal_http_error,
            logger=logger,
        )
        def _attempt():
            with self._session.get(url, stream=True, timeout=self._timeout) as response:
                response.raise_for_status()
                target.parent.mkdir(parents=True, exist_ok=True)
                # Unique tmp name: concurrent downloads of the same URL must not collide
                unique_suffix = f"{target.suffix}.{uuid.uuid4().hex}.part"
                tmp_path = target.with_suffix(unique_suffix)
                with open(tmp_path, "wb") as fh:
                    for chunk in response.iter_content(chunk_size=DL_CHUNCK_SIZE):
                        if chunk:
                            fh.write(chunk)
                tmp_path.replace(target)

        _attempt()
