
BNAME:=$(shell  date +'OLD/sodasw-backup-%Y%m%d-%H%M')
BNAME_C=${BNAME}-code.tar.gz


all:
	cd src && MAKELEVEL= make all

install:
	cd src && MAKELEVEL= make install

clean:
	rm -rf *~ *.o doc/*~
	cd src && MAKELEVEL= make clean

backup: clean
	tar cfz ${BNAME_C} -C .. `basename $$(pwd)` --exclude=OLD/sodasw-backup\* \
        --exclude=bin/\*serv
	ls -lh ${BNAME_C}



