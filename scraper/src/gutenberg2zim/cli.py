"""Command-line interface (split out of `entrypoint.py`).

Only argument parsing lives here: `parse_args()` turns `sys.argv` into a
docopt result, `main()` builds a `ScrapeConfig` from it and hands it to
`run_scrape()`. Everything else is in `config.py` / `orchestrator.py`.
"""

from docopt import docopt

from gutenberg2zim.config import build_scrape_config
from gutenberg2zim.constants import VERSION
from gutenberg2zim.orchestrator import run_scrape

help_info = (
    """Usage: gutenberg2zim [--overwrite] [--source SOURCE] [-l LANGS] """
    """[-f FORMATS] [-z ZIM_PATH] [-b BOOKS] """
    """[-t ZIM_TITLE] [-n ZIM_DESC] [-L ZIM_LONG_DESC] """
    """[--zim-languages LANGUAGES] [--zim-name ZIM_NAME] [-c CONCURRENCY] """
    """[--no-index] [--title-search] [--lcc-shelves SHELVES] """
    """[--stats-filename STATS_FILENAME] [--publisher ZIM_PUBLISHER] """
    """[--mirror-url MIRROR_URL] [--output OUTPUT_FOLDER] """
    """[--primary-color COLOR] [--secondary-color COLOR] """
    """[--ui-dist UI_DIST] [--debug] """
    """

-h --help                       Display this help message
--overwrite                     Overwrite ZIM file if target already exists
--source=<source>               Source to scrape (gutenberg) [default: gutenberg]

-l --languages=<list>           Comma-separated list of lang codes to filter"""
    """ export to (preferably ISO 639-1, else ISO 639-3)
-f --formats=<list>             Comma-separated list of formats to filter """
    """export to (epub, html, pdf, all)

-z --zim-file=<file>            Write ZIM into at this file path
--zim-name=<name>               Set ZIM name (metadata)
-t --zim-title=<title>          Set ZIM title
-n --zim-desc=<description>         Set ZIM description
-L --zim-long-desc=<description>   Set ZIM long description
--zim-languages=<languages>          Set ZIM Language metadata

-b --books=<ids>                Execute the processes for specific books, """
    """separated by commas, or dashes for intervals
-c --concurrency=<nb>           Number of concurrent process for processing """
    """tasks
--no-index                      Do NOT create full-text index within ZIM file
--title-search                  Add field to search a book by title and directly """
    """jump to it
--lcc-shelves=<shelves>         Comma-separated list of LCC shelf codes to include """
    """(e.g., P,PR,Q). Use 'all' to generate all shelves. If omitted, no shelf generated
--stats-filename=<filename>  Path to store the progress JSON file to
--publisher=<zim_publisher>     Custom Publisher in ZIM Metadata (openZIM otherwise)
--mirror-url=<mirror_url>       Optional custom url of mirror hosting the source files
--output=<output_folder>        Output folder for ZIMs. Default: ./output
--primary-color=<color>         Custom primary color. Hex/HTML syntax (#1976D2)
--secondary-color=<color>       Custom secondary color. Hex/HTML syntax (#424242)
--ui-dist=<ui_dist>              Directory containing Vue.js UI build output (ui/dist).
                                 Default: ../ui/dist or GUTENBERG_UI_DIST env var
--debug                         Enable verbose output

This script is used to produce a ZIM file from a book source (Project Gutenberg
by default) using a mirror.
The scraper will download the catalog and metadata files, parse metadata, download
books, and create the ZIM file."""
)


def parse_args() -> dict:
    """Parse command-line arguments with docopt"""
    return docopt(help_info, version=VERSION)


def main():
    arguments = parse_args()
    config = build_scrape_config(arguments)
    run_scrape(config)
