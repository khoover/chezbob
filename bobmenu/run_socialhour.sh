#!/bin/bash

DIR=`dirname $0`

trap '' INT
while true; do
    $DIR/socialhour.pl
done
