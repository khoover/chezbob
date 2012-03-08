include ../sodacom.in

SCRIPTS=controller.pl ctool cprocman stockcount-serv.pl freevend-serv.pl uictrl-serv.pl barcode-serv.pl backend.py sodagui.py bobdb-serv.pl invert_touchscreen_axes.sh
EXTRA=sodagui-bg.png

all:

install: 
	install -m 555 ${SCRIPTS} ${BIN}
	chown kiosk:devel ${BIN}/cprocman
	chmod ug+s,o-x ${BIN}/cprocman
	install -m 444 ${EXTRA} ${BIN}

clean:
	rm -f *~

