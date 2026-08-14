"""Command-line interface (split out of `entrypoint.py`).

Only argument parsing lives here: `parse_args()` turns `sys.argv` into a
docopt result, `main()` builds a `ScrapeConfig` from it and hands it to
`run_scrape()`. Everything else is in `config.py` / `orchestrator.py`.
"""

from docopt import docopt

from gutenberg2zim.config import build_scrape_config
from gutenberg2zim.constants import VERSION
from gutenberg2zim.orchestrator import run_scrape
from gutenberg2zim.sources.registry import SOURCES

source_options_help = "\n".join(profile.cli_options for profile in SOURCES.values())

help_info = f"""Usage: gutenberg2zim [options]

Options:
  -h --help                       Display this help message
  --overwrite                     Overwrite ZIM file if target already exists
  --source=<source>               Source slug [default: gutenberg]
  -l --languages=<list>           Comma-separated language codes
  -f --formats=<list>             Formats: epub, html, pdf, or all
  -z --zim-file=<file>            ZIM output path
  --zim-name=<name>               ZIM metadata name
  -t --zim-title=<title>          ZIM title
  -n --zim-desc=<description>     ZIM description
  -L --zim-long-desc=<description> ZIM long description
  --zim-languages=<languages>     ZIM language metadata
  -b --books=<ids>                Source catalog positions or ranges
  -c --concurrency=<nb>           Concurrent processing tasks
  --no-index                      Disable the full-text index
  --title-search                  Enable title search
  {source_options_help}
  --stats-filename=<filename>     Progress JSON path
  --publisher=<publisher>         ZIM publisher [default: openZIM]
  --mirror-url=<mirror_url>       Source mirror URL
  --output=<output_folder>        Output directory [default: ./output]
  --cache-dir=<cache_folder>      Persist caches here; pass again to reuse them
  --primary-color=<color>         Custom primary color
  --secondary-color=<color>       Custom secondary color
  --ui-dist=<ui_dist>             Vue UI distribution directory
  --debug                         Enable verbose output
"""


def parse_args() -> dict:
    """Parse command-line arguments with docopt"""
    return docopt(help_info, version=VERSION)


def main():
    arguments = parse_args()
    config = build_scrape_config(arguments)
    run_scrape(config)
