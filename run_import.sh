#!/bin/bash

set -e
set -u

SITE_ROOT=.

IMPORT_ROOT=$SITE_ROOT/import_script

#cd
#if [ $PWD != "/home/users/cubetoolkit" ]; then
#	echo "Something's not right here"
#	exit 2
#fi

cd $SITE_ROOT

pushd $IMPORT_ROOT/
echo "Rsyncing data off sparror"
./get_data.sh
popd

echo "Loading data into intermediate import database"
pushd $IMPORT_ROOT/basic_load/
./data_import.rb
popd

echo "Loading into django"
mv logging.conf logging.disabled.conf
cp logging.debug.conf logging.conf
$IMPORT_ROOT/import .
rm logging.conf
mv logging.disabled.conf logging.conf
echo

echo "Done!"

