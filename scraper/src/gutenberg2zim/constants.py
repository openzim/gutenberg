import logging
import os
import pathlib

from zimscraperlib.logging import getLogger

from gutenberg2zim.__about__ import __version__

ROOT_DIR = pathlib.Path(__file__).parent
NAME = ROOT_DIR.name

VERSION = __version__

SCRAPER = f"{NAME} {VERSION}"

logger = getLogger(NAME, level=logging.INFO)

FAVICON_PATH = ROOT_DIR / "templates" / "favicon.png"
with open(FAVICON_PATH, "rb") as f:
    FAVICON_BYTES = f.read()

DEFAULT_HTTP_TIMEOUT = 10
DL_CHUNCK_SIZE = 8192

LOCALES_LOCATION = pathlib.Path(os.getenv("LOCALES_LOCATION", "./locales"))
