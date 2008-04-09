

include sodacom.in

all:
	make -C lib all
	make -C mdb-server all
	make -C vmc-server all
	make -C fp-server all
	make -C scripts all

install:
	mkdir -p ${BIN}
	mkdir -p ${BIN}/../conf
	mkdir -p ${BIN}/../lib
	make -C mdb-server install
	make -C vmc-server install
	make -C fp-server install
	make -C scripts install
	make -C lib install


clean:
	rm -rf *~ *.o doc/*~
	cd mdb-server && MAKELEVEL= make clean
	cd vmc-server && MAKELEVEL= make clean
	cd fp-server && MAKELEVEL= make clean
	cd scripts && MAKELEVEL= make clean
	cd lib && MAKELEVEL= make clean





