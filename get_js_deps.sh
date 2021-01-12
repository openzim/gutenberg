#!/bin/sh

###
# download JS dependencies and place them in our templates/datatables folder
###

if ! command -v curl > /dev/null; then
	echo "you need curl."
	exit 1
fi

# Absolute path this script is in.
SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"
TEMPLATE_PATH="${SCRIPT_PATH}/gutenbergtozim/templates"

echo "About to download JS assets to ${TEMPLATE_PATH}/datatables"

echo "getting datatables.min.css"
curl -L -O https://cdn.datatables.net/v/dt/dt-1.10.13/r-2.1.1/datatables.min.css
rm -rf $TEMPLATE_PATH/datatables
mkdir -p $TEMPLATE_PATH/datatables
mv datatables.min.css $TEMPLATE_PATH/datatables
rm -f datatables.min.css
echo "getting datatables.min.js"
curl -L -O https://cdn.datatables.net/v/dt/dt-1.10.13/r-2.1.1/datatables.min.js
mv datatables.min.js $TEMPLATE_PATH/datatables
rm -f datatables.min.js
echo "getting datatables.js"
curl -L -O https://cdn.datatables.net/v/dt/dt-1.10.13/r-2.1.1/datatables.js
mv datatables.js $TEMPLATE_PATH/datatables
rm -f datatables.js
echo "getting datatables.css"
curl -L -O https://cdn.datatables.net/v/dt/dt-1.10.13/r-2.1.1/datatables.css
mv datatables.css $TEMPLATE_PATH/datatables
rm -f datatables.css

