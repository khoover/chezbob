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
