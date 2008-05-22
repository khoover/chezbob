include ../sodacom.in

SCRIPTS=controller.pl ctool cprocman stockcount-serv.pl freevend-serv.pl uictrl-serv.pl barcode-serv.pl backend backend.py sodagui.py bobdb-serv.pl
EXTRA=sodagui-bg.png

all:

install: 
	install -m 555 ${SCRIPTS} ${BIN}
	chown kiosk:devel ${BIN}/cprocman
	chmod ug+s,o-x ${BIN}/cprocman
	install -m 444 ${EXTRA} ${BIN}

clean:
	rm -f *~

