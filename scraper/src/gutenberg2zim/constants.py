import logging
import pathlib

from zimscraperlib.logging import getLogger

from gutenberg2zim.__about__ import __version__

PROJECT_ROOT = pathlib.Path(__file__).parents[3]
ROOT_DIR = pathlib.Path(__file__).parent
NAME = ROOT_DIR.name

VERSION = __version__

SCRAPER = f"{NAME} {VERSION}"

logger = getLogger(NAME, level=logging.INFO)

TMP_FOLDER = "tmp"
TMP_FOLDER_PATH = pathlib.Path(TMP_FOLDER).resolve()


FAVICON_PATH = ROOT_DIR / "assets" / "favicon.png"
with open(FAVICON_PATH, "rb") as f:
    FAVICON_BYTES = f.read()

DEFAULT_HTTP_TIMEOUT = 10
DL_CHUNCK_SIZE = 8192
