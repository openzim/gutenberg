# Gutenberg Offline
This scraper downloads the whole [Project
Gutenberg](https://www.gutenberg.org) library and puts it in a
[ZIM](https://openzim.org) file, a clean and user friendly format for
storing content for offline usage.

[![CodeFactor](https://www.codefactor.io/repository/github/openzim/gutenberg/badge)](https://www.codefactor.io/repository/github/openzim/gutenberg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![codecov](https://codecov.io/gh/openzim/gutenberg/branch/main/graph/badge.svg)](https://codecov.io/gh/openzim/gutenberg)
[![PyPI version shields.io](https://img.shields.io/pypi/v/gutenberg2zim.svg)](https://pypi.org/project/gutenberg2zim/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gutenberg2zim.svg)](https://pypi.org/project/gutenberg2zim/)
[![Docker](https://ghcr-badge.egpl.dev/openzim/gutenberg/latest_tag?label=docker)](https://ghcr.io/openzim/gutenberg)

> [!WARNING]  
> This scraper is now known to have a serious flaw. A critical bug https://github.com/openzim/gutenberg/issues/219 has been discovered which leads to incomplete archives. Work on https://github.com/openzim/gutenberg/issues/97 (complete rewrite of the scraper logic) now seems mandatory to fix these annoying problems. We however currently miss the necessary bandwidth to address these changes. Help is of course welcomed, but be warned this is going to be a significant project (at least 10 man.days to change the scraper logic so that we can fix the issue I would say, so probably the double since human is always bad at estimations).

## Coding guidelines
Main coding guidelines comes from the [openZIM Wiki](https://github.com/openzim/overview/wiki)

### Setting up the environment

Here we will setup everything needed to run the source version from your machine, supposing you want to modify it. If you simply want to run the tool, you should either install the PyPi package or use the Docker image. Docker image can also be used for development but needs a bit of tweaking for live reload of your code modifications.

### Install the dependencies

First, ensure you use the proper Python version, inline with the requirement of `pyproject.toml` (you might for instance use `pyenv` to manage multiple Python versions in parallel).

You then need to install the various tools/libraries needed by the scraper.

#### GNU/Linux

```
sudo apt-get install python-pip python-dev libxml2-dev libxslt-dev advancecomp jpegoptim pngquant p7zip-full gifsicle curl zip zim-tools
```

#### macOS

```
brew install advancecomp jpegoptim pngquant p7zip gifsicle
```

### Setup the package

First, clone this repository.

```bash
git clone git@github.com:kiwix/gutenberg.git
cd gutenberg
```

If you do not already have it on your system, install `hatch` to build the software and manage virtual environments (you might be interested by our detailed [Developer Setup](https://github.com/openzim/_python-bootstrap/wiki/Developer-Setup) as well).

```bash
pip3 install hatch
```

Start a hatch shell: this will install software including dependencies in an isolated virtual environment.

```bash
hatch shell
```

That's it. You can now run `gutenberg2zim` from your terminal.

## Getting started

After setting up the whole environment you can just run the main
script `gutenberg2zim`.  It will download, process and export the
content.

```bash
./gutenberg2zim
```

#### Arguments

You can also specify parameters to customize the content.  Only want
books with the Id 100-200? Books only in French? English? Or only
those both? No problem!  You can also include or exclude book
formats. You can add bookshelves and the option to search books by
title to enrich your user experince.

```bash
./gutenberg2zim -l en,fr -f pdf --books 100-200 --bookshelves --title-search
```

This will download books in English and French that have the Id 100 to
200 in the HTML (default) and PDF format.

You can find the full arguments list below:

```bash
-h --help                       Display this help message
-y --wipe-db                    Empty cached book metadata
-F --force                      Redo step even if target already exist

-l --languages=<list>           Comma-separated list of lang codes to filter export to (preferably ISO 639-1, else ISO 639-3)
-f --formats=<list>             Comma-separated list of formats to filter export to (epub, html, pdf, all)

-e --static-folder=<folder>     Use-as/Write-to this folder static HTML
-z --zim-file=<file>            Write ZIM into this file path
-t --zim-title=<title>          Set ZIM title
-n --zim-desc=<description>     Set ZIM description
-d --dl-folder=<folder>         Folder to use/write-to downloaded ebooks
-u --rdf-url=<url>              Alternative rdf-files.tar.bz2 URL
-b --books=<ids>                Execute the processes for specific books, separated by commas, or dashes for intervals
-c --concurrency=<nb>           Number of concurrent process for processing tasks
--dlc=<nb>                      Number of concurrent *download* process for download (overwrites --concurrency). if server blocks high rate requests
-m --one-language-one-zim=<folder> When more than 1 language, do one zim for each   language (and one with all)
--no-index                      Do NOT create full-text index within ZIM file
--check                         Check dependencies
--prepare                       Download rdf-files.tar.bz2
--parse                         Parse all RDF files and fill-up the DB
--download                      Download ebooks based on filters
--zim                           Create a ZIM file
--title-search                  Add field to search a book by title and directly jump to it
--bookshelves                   Add bookshelves
--optimization-cache=<url>      URL with credentials to S3 bucket for using as optimization cache
--use-any-optimized-version     Try to use any optimized version found on optimization cache
```

## Screenshots

![](https://raw.githubusercontent.com/openzim/gutenberg/main/pictures/screenshot_1.png)
![](https://raw.githubusercontent.com/openzim/gutenberg/main/pictures/screenshot_2.png)

## License

[GPLv3](https://www.gnu.org/licenses/gpl-3.0) or later, see
[LICENSE](LICENSE) for more details.
