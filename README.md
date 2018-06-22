# Project Gutenberg Offline

[![](https://img.shields.io/pypi/v/gutenberg2zim.svg)](https://pypi.python.org/pypi/gutenberg2zim)

A scraper that downloads the whole repository of [Project Gutenberg]
(http://www.gutenberg.org) and puts it into a locally browsable
directory and then in a ZIM file (http://www.openzim.org), a clean and
user friendly format for storing content for offline usage. It was
created during a Kiwix Hackathon in Lyon, France in July 2014.

## Setting up the environment

It's recommended that you use `virtualenv`. `py2.7.x` and `py3.6+` are supported.

### Install the dependencies

#### Linux 

```
sudo apt-get install python-pip python-dev libxml2-dev libxslt-dev advancecomp jpegoptim pngquant p7zip-full gifsicle curl zip
sudo pip install virtualenv
```

#### Mac OS X

```
sudo easy_install pip
sudo pip install virtualenv
brew install advancecomp jpegoptim pngquant p7zip gifsicle
```

### Set up the project

```
git clone git@github.com:kiwix/gutenberg.git
cd gutenberg
virtualenv gut-env (or any name you want)
./gut-env/bin/pip install -r requirements.pip
```

### Working in the environment

* Activate the environment:  `source gut-env/bin/activate`
* Quit the environment: `deactivate`

## Getting started

After setting up the whole environment you can just run the main script `gutenberg2zim`.   
It will download, process and export the content.

```
./gutenberg2zim
```

#### Arguments

You can also specify parameters to customize the content.   
Only want books with the Id 100-200? Books only in French? English? Or only those both? No problem!  
You can also include or exclude book formats.

```
./gutenberg2zim -l en,fr -f pdf --books 100-200
```
This will download English and French books that have the Id 100 to 200 in the html (default) and pdf format.

You can find the full arguments list below.

``` sh
-h --help                       Display this help message
-y --wipe-db                    Do not wipe the DB during parse stage
-F --force                      Redo step even if target already exist

-l --languages=<list>           Comma-separated list of lang codes to filter export to (preferably ISO 639-1, else ISO 639-3)
-f --formats=<list>             Comma-separated list of formats to filter export to (epub, html, pdf, all)

-m --mirror=<url>               Use URL as base for all downloads.
-r --rdf-folder=<folder>        Don't download rdf-files.tar.bz2 and use extracted folder instead
-e --static-folder=<folder>     Use-as/Write-to this folder static HTML
-z --zim-file=<file>            Write ZIM into this file path
-t --zim-title=<title>          Set ZIM title
-n --zim-desc=<description>     Set ZIM description
-d --dl-folder=<folder>         Folder to use/write-to downloaded ebooks
-u --rdf-url=<url>              Alternative rdf-files.tar.bz2 URL
-b --books=<ids>                Execute the processes for specific books, separated by commas, or dashes for intervals
-c --concurrency=<nb>           Number of concurrent process for download and parsing tasks
--dlc=<nb>                      Number of concurrent *download* process for download (overwrites --concurrency). if server blocks high rate requests
--one-language-one-zim          When more than 1 language, do one zim for each   language (and one with all)
-x --zim-title=<title>          Custom title for the ZIM file
-q --zim-desc=<desc>            Custom description for the ZIM file
--no-index                      Do NOT create full-text index within ZIM file


-x --zim-title=<title>          Custom title for the ZIM file
-q --zim-desc=<desc>            Custom description for the ZIM file

--check                         Check dependencies
--prepare                       Download & extract rdf-files.tar.bz2
--parse                         Parse all RDF files and fill-up the DB
--download                      Download ebooks based on filters
--export                        Export downloaded content to zim-friendly static HTML
--dev                           Exports *just* Home+JS+CSS files (overwritten by --zim step)
--zim                           Create a ZIM file
```


## Screenshots

![](http://i.imgur.com/A4NnS2K.png?1)

![](http://i.imgur.com/mtZduCM.png?2)
