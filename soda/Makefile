
BNAME:=$(shell  date +'OLD/sodasw-backup-%Y%m%d-%H%M')
BNAME_C=${BNAME}-code.tar.gz


all:
	cd src && MAKELEVEL= make all docs

dpfp:
	cd libs/libdpfp-0.2.2 && ./configure && MAKELEVEL= make

dpfp-install:
	cd libs/libdpfp-0.2.2 && MAKELEVEL= make install

install:
	cd stuff-to-copy && MAKELEVEL= make install
	cd libs/libdpfp-0.2.2 && MAKELEVEL= make install
	cd src && MAKELEVEL= make install

docs:
	cd src && MAKELEVEL= make docs

clean:
	rm -rf *~ *.o doc/*~
	cd src && MAKELEVEL= make clean
	cd libs/libdpfp-0.2.2 && MAKELEVEL= make clean

backup: clean
	tar cfz ${BNAME_C} -C .. `basename $$(pwd)` --exclude=OLD/sodasw-backup\* \
        --exclude=bin/\*serv
	ls -lh ${BNAME_C}



