import logging
import pathlib

from zimscraperlib.logging import getLogger

from gutenberg2zim.__about__ import __version__

ROOT_DIR = pathlib.Path(__file__).parent
NAME = ROOT_DIR.name

VERSION = __version__

SCRAPER = f"{NAME} {VERSION}"

# check-> this is for only temporary used.
FAVICON_PATH = pathlib.Path(__file__).parent / "public" / "favicon_temp.png"
with open(FAVICON_PATH, "rb") as f:
    FAVICON_BYTES = f.read()

logger = getLogger(NAME, level=logging.INFO)

TMP_FOLDER = "tmp"
current_file = pathlib.Path(__file__).resolve()
PROJECT_ROOT = current_file.parents[3]
TMP_FOLDER_PATH = (PROJECT_ROOT / "zimui" / "public" / "tmp").resolve()

DEFAULT_HTTP_TIMEOUT = 10
DL_CHUNCK_SIZE = 8192
