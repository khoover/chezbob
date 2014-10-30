#! /usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE=$DIR/../

function installPkg {
  echo "Installing $1"
  dpkg -s $1 &> /dev/null
  if [[ $? -ne 0 ]]; then
    echo "Package $1 not installed. Installing. This may request your superuser password"
    sudo apt-get install $1
  else
    echo "Package $1 is already installed."
  fi
}

function installGlobNpmPkg {
  echo "Installing npm package $1 globally. This may request your superuser password"
  sudo npm install -g $1
}

installPkg ruby-sass
installPkg redis-server
installPkg nodejs
installPkg nodejs-legacy
installPkg socat

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
scp soda:/home/dimo/app.db $BASE/deploy/
