include ../sodacom.in

SCRIPTS=controller.pl ctool cprocman stockcount-serv.pl freevend-serv.pl uictrl-serv.pl barcode-serv.pl backend

all:

install: 
	install -m 555 ${SCRIPTS} ${BIN}
	@#install -m 555 sodacom.conf ${BIN}/../conf
	ln -sf `pwd`/sodacom.conf ${BIN}/../conf
	install -m 444 ${VLIBDIR}/*.pm ${BIN}/../lib
	chown kiosk:devel ${BIN}/cprocman
	chmod ug+s,o-x ${BIN}/cprocman

clean:
	rm -f *~

