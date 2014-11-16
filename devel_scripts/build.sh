#! /usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE=$DIR/../

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
