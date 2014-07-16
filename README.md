# gutenberg

A scraper that downloads the whole repository of [Project Gutenberg](http://www.gutenberg.org).  
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
