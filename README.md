gutenberg
=========

Gutenberg Kiwix Scraper for Lyon Hackathon


Setting the environement
------------------------

Using virtualenv.

Setting the system:
* sudo apt-get install python-pip python-dev libxml2-dev libxslt-dev
* sudo pip install virtualenvwrapper
* add in your .bashrc:

  source /usr/local/bin/virtualenvwrapper.sh

Setting the environment:
* git clone git@github.com:kiwix/gutenberg.git
* cd gutenberg
* mkvirtualenv gut (or any name you want)
(and you are in the container created by virtualenv)

Working in the environment:
* Activate the environment: workon gut
* Quit the environment: deactivate
* Install dependancies in the environment: pip install -r requirements.pip

