#! /usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE=$DIR/../

MDB=false
VDB=false
BARCODE=false
BARCODEI=false
SODA=false

if [[ $# -gt 1 ]]; then 
	echo "Usage: $0 [mdb|vdb|barcode|barcodei|soda]"
	exit -1
fi

if [[ $# -eq 0 ]]; then 
	MDB=true
	VDB=true
	BARCODE=true
	BARCODEI=true
	SODA=true
else
	if [[ $1 == "mdb" ]] ; then
		MDB=true
	elif [[ $1 == "vdb" ]] ; then 
		VDB=true
	elif [[ $1 == "barcode" ]] ; then 
		BARCODE=true
	elif [[ $1 == "barcodei" ]] ; then 
		BARCODEI=true
	elif [[ $1 == "soda" ]] ; then 
		SODA=true
	else
		echo "Error: bad argument"
		exit -1
	fi
fi

if $MDB ; then
	pushd $BASE/bob2k14/mdb_server
	npm cache clean
	npm install
	./node_modules/gulp/bin/gulp.js
	popd
fi

if $VDB ; then
	pushd $BASE/bob2k14/vdb_server
	npm cache clean
	npm install
	./node_modules/gulp/bin/gulp.js
	popd
fi

if $BARCODE ; then
	pushd $BASE/bob2k14/barcode_server
	npm cache clean
	npm install
	./node_modules/gulp/bin/gulp.js
	popd
fi

if $BARCODEI ; then
	pushd $BASE/bob2k14/barcodei_server
	npm cache clean
	npm install
	./node_modules/gulp/bin/gulp.js
	popd
fi

if $SODA ; then
	pushd $BASE/bob2k14/soda_server
	npm cache clean
	npm install
	./node_modules/gulp/bin/gulp.js
	popd
fi
