#! /usr/bin/env bash

me=`whoami`

if [[ $me != "root" ]] ; then
    echo "Must be ran as root";
    exit -1;
fi

service cb_sodad restart
service cb_barcoded restart
service cb_mdbd restart
service cb_vdbd restart
