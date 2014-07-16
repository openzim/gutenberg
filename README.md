# gutenberg

A scraper that downloads the whole repository of [Project Gutenberg](http://www.gutenberg.org) and puts it into a clean and user friendly format.  
It was created during the Kiwix Hackathon in Lyon, France in May 2014.


## Setting up the environement

It's reccommened that you use `virtualenv`.

### Install the dependencies

#### Linux

```
sudo apt-get install python-pip python-dev libxml2-dev libxslt-dev advancecomp jpegoptim pngquant p7zip-full gifsicle
sudo pip install virtualenvwrapper
```

#### Mac OS X

```
sudo easy_install pip
sudo pip install virtualenvwrapper
brew install advancecomp jpegoptim pngquant p7zip gifsicle
```

Finally, Add this to your `.bashrc`:

```
source /usr/local/bin/virtualenvwrapper.sh
```

### Set up the project

```
git clone git@github.com:kiwix/gutenberg.git
cd gutenberg
mkvirtualenv gut (or any name you want)
```

### Working in the environment

* Activate the environment:  `workon gut`
* Quit the environment: `deactivate`
* Install the python dependencies: `pip install -r requirements.pip`

## Getting started

After setting up the whole enviroment you can just run the main script `dump-gutenberg.py`.   
It will download, process and export the content.

```
./dump-gutenberg.py 
```

#### Arguments

You can also specify parameters to customize the content.   
Only want books with the Id 100-200? Books only in French? English? Or only those both? No problem!  
You can also include or exclude book formats.

```
./dump-gutenberg.py -l en,fr -f pdf --books 100-200
```
This will download English and French books that have the Id 100 to 200 in the html(default) and pdf format.

You can find the full arguments list below.

```
-h --help                       Display this help message
-k --keep-db                    Do not wipe the DB during parse stage

-l --languages=<list>           Comma-separated list of lang codes to filter export to
-f --formats=<list>             Comma-separated list of formats to filter export to (pdf, epub, all)

-m --mirror=<url>               Use URL as base for all downloads.
-r --rdf-folder=<folder>        Don't download rdf-files.tar.bz2 and use extracted folder instead
-e --static-folder=<folder>     Use-as/Write-to this folder static HTML
-z --zim-file=<file>            Write ZIM into this file path
-d --dl-folder=<folder>         Folder to use/write-to downloaded ebooks
-u --rdf-url=<url>              Alternative rdf-files.tar.bz2 URL
-b --books=<ids>                Execute the processes for specific books, separated by commas or dashes

-x --zim-title=<title>          Custom title for the ZIM file
-q --zim-desc=<desc>            Custom description for the ZIM file

--check                         Check dependencies
--prepare                       Download & extract rdf-files.tar.bz2
--parse                         Parse all RDF files and fill-up the DB
--download                      Download ebooks based on filters
--export                        Export downloaded content to zim-friendly static HTML
--zim                           Create a ZIM file
```


## Screenshots 

![](http://i.imgur.com/A4NnS2K.png?1)

![](http://i.imgur.com/mtZduCM.png?2)
