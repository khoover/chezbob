#! /usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE=$DIR/../
OUT=dump.sql

if [[ $# -eq 1 ]] ; then
  OUT=$1
fi

ssh -C dimo@soda.ucsd.edu -p 425 pg_dump -U bob --inserts bob \
	-t bulk_items                \
	-t floor_locations           \
	-t historical_prices         \
	-t inventory                 \
	-t messages                  \
	-t product_source            \
	-t products                  \
	-t profiles                  \
	-t roles                     \
	-t soda_inventory            \
	-t transactions              \
	-t ucsd_emails               \
	-t user_balances_20140305    \
	-t userbarcodes              \
	-t users                     \
  > $OUT

