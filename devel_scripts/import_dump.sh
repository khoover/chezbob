#! /usr/bin/env bash

if [[ $# -ne 1 ]] ; then
	echo "Usage $0 dump.sql"
	exit -1
fi

sudo -u postgres psql -f $1
