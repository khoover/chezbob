#! /usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE=$DIR/../

virtualenv --python=python3.4 $BASE/deploy

source $BASE/deploy/bin/activate

pip install docopt
pip install flask
pip install flask_jsonrpc
pip install sqlalchemy
pip install flask-sqlalchemy
pip install flask-cors
pip install requests
pip install sqlalchemy-migrate
pip install pyserial
pip install sarge
pip install nodeenv

nodeenv -p

deactivate
source $BASE/deploy/bin/activate

npm install -g forever 
npm install -g gulp 
npm install -g typescript
npm install -g bunyan

pushd $BASE/bob2k14/mdb_server
npm install
gulp
popd

pushd $BASE/bob2k14/vdb_server
npm install
gulp
popd

#pushd $BASE/bob2k14/soda_server
#npm install
#gulp
#popd

echo "Attempting to copy test app.db from soda"
echo "Please ensure you've setup an entry for soda in your .ssh/config"

scp soda:/home/dimo/app.db $BASE/deploy/
