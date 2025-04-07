=============
gutenberg2zim
=============

A scraper that downloads the whole repository of [Project Gutenberg]
(http://www.gutenberg.org) and puts it into a locally browsable
directory and then in a ZIM file (http://www.openzim.org), a clean and
user friendly format for storing content for offline usage.

------------
Dependencies
------------
 For Users: Running the Scraper
-------------

Ubuntu/Debian for scraper only
-------------

 .. code-block:: sh
	sudo apt update && sudo apt install -y python3-pip p7zip-full zip zim-tools curl jpegoptim pngquant

Fedora for scraper
------
.. code-block:: sh
	sudo dnf install -y python3-pip jpegoptim pngquant p7zip curl zip zim-tools

Arch Linux
----------
.. code-block:: sh
	sudo pacman -S python-pip libxml2 jpegoptim pngquant p7zip curl zip zim-tools
macOS
-----

.. code-block:: sh

    brew install advancecomp jpegoptim pngquant p7zip gifsicle

------

 For Developers: Contributing & Modifying
-------------
Ubuntu
-------------
.. code-block:: sh

    sudo apt update && sudo apt install -y python3-pip libxml2-dev libxslt-dev jpegoptim pngquant p7zip-full curl zip zim-tools

Fedora
------
.. code-block:: sh

    sudo dnf install -y python3-pip libxml2-devel libxslt-devel jpegoptim pngquant p7zip curl zip zim-tools

Arch Linux
----------
.. code-block:: sh

    sudo pacman -Syu python-pip libxml2 libxslt jpegoptim pngquant p7zip curl zip zim-tools

macOS
-----

.. code-block:: sh

    brew install  libxml2 libxslt advancecomp jpegoptim pngquant p7zip gifsicle

------
Usage
------

.. code-block:: sh

	gutenberg2zim

By default (no argument), it runs all the steps: download, parse, export and zim.

.. code-block:: sh

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
	-L --zim-long-desc=<description> Set ZIM long description
	-d --dl-folder=<folder>         Folder to use/write-to downloaded ebooks
	-u --rdf-url=<url>              Alternative rdf-files.tar.bz2 URL
	-b --books=<ids>                Execute the processes for specific books, separated by commas, or dashes for intervals
	-c --concurrency=<nb>           Number of concurrent process for download and parsing tasks
	-x --zim-title=<title>          Custom title for the ZIM file
	-q --zim-desc=<desc>            Custom description for the ZIM file
	--check                         Check dependencies
	--prepare                       Download & extract rdf-files.tar.bz2
	--parse                         Parse all RDF files and fill-up the DB
	--download                      Download ebooks based on filters
	--export                        Export downloaded content to zim-friendly static HTML
	--dev                           Exports *just* Home+JS+CSS files (overwritten by --zim step)
	--zim                           Create a ZIM file
