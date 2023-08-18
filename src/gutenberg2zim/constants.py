import logging
import pathlib

from zimscraperlib.logging import getLogger

from gutenberg2zim.__about__ import __version__

ROOT_DIR = pathlib.Path(__file__).parent
NAME = ROOT_DIR.name

VERSION = __version__

SCRAPER = f"{NAME} {VERSION}"

# when modifiying this list, update list in hatch_build.py as well
JS_DEPS: list[str] = [
    "datatables/datatables.min.css",
    "datatables/datatables.min.js",
]

logger = getLogger(__name__, level=logging.DEBUG)

TMP_FOLDER = "tmp"
TMP_FOLDER_PATH = pathlib.Path(TMP_FOLDER)
