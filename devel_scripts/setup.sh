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

# Set the permissions on the postgresql server to allow all connections
# from localhost
echo "Setting permissions for postgresql database. This may ask your sudo password"
echo "
local   all             postgres                                peer

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# local is for Unix domain socket connections only
local   all             all                                     trust
# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
# IPv6 local connections:
host    all             all             ::1/128                 md5
" |  sudo tee /etc/postgresql/9.3/main/pg_hba.conf 
