#! /usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE=$DIR/../

function installPkg {
  dpkg -s $1 &> /dev/null
  if [[ $? -ne 0 ]]; then
    echo "Installing $1. This may request your superuser password"
    sudo apt-get install $1
  else
    echo "Package $1 is already installed."
  fi
}

function installGlobNpmPkg {
  # First check if package is already globally installed
  npm list -g | grep "$1@" > /dev/null
  if [[ $? -ne 0 ]]; then 
    echo "Installing npm package $1 globally. This may request your superuser password"
    sudo npm install $1 -g 
  else
    echo "Npm package $1 is already globally installed"
  fi
}

installPkg ruby-sass
installPkg redis-server
installPkg nodejs
installPkg nodejs-legacy
installPkg socat
installPkg libpq-dev


installGlobNpmPkg forever
installGlobNpmPkg gulp
installGlobNpmPkg typescript 
installGlobNpmPkg bunyan
installGlobNpmPkg sqlite3

pushd $BASE/bob2k14/mdb_server
npm install
gulp
popd

pushd $BASE/bob2k14/vdb_server
npm install
gulp
popd

pushd $BASE/bob2k14/barcode_server
npm install
gulp
popd

pushd $BASE/bob2k14/barcodei_server
npm install
gulp
popd

pushd $BASE/bob2k14/soda_server
npm install
gulp
popd

pushd $BASE/devel_scripts
npm install optimist
npm install serialport
popd

echo "Attempting to copy test app.db from soda"
echo "Please ensure you've setup an entry for soda in your .ssh/config"

mkdir $BASE/deploy
scp soda.ucsd.edu:/home/dimo/app.db $BASE/deploy/
