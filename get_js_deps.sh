#!/bin/sh

set -e

###
# download JS dependencies and place them in our templates/assets folder
# then launch our ogv.js script to fix dynamic loading links
###

if ! command -v curl > /dev/null; then
	echo "you need curl."
	exit 1
fi

# Absolute path this script is in.
SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"
ASSETS_PATH="${SCRIPT_PATH}/src/gutenberg2zim/templates"

echo "About to download JS assets to ${ASSETS_PATH}"

echo "getting datatables.min.js"
curl -L -O https://cdn.datatables.net/v/dt/dt-1.13.6/r-2.5.0/datatables.min.js
rm -rf $ASSETS_PATH/datatables/datatables.min.js
mv datatables.min.js $ASSETS_PATH/datatables/datatables.min.js

echo "getting datatables.min.css"
curl -L -O https://cdn.datatables.net/v/dt/dt-1.13.6/r-2.5.0/datatables.min.css
rm -rf $ASSETS_PATH/datatables/datatables.min.css
mv datatables.min.css $ASSETS_PATH/datatables/datatables.min.css

echo "getting jquery-1.11.1.min.js"
curl -L -O https://code.jquery.com/jquery-1.11.1.min.js
rm -rf $ASSETS_PATH/jquery/jquery-1.11.1.min.js
mv jquery-1.11.1.min.js $ASSETS_PATH/jquery/jquery-1.11.1.min.js
