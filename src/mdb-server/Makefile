
APPNAME=mdbserv
include ../sodacom.in

all: ${APPNAME}

install: ${APPNAME}
	cp ${APPNAME} ${BIN}

run: all
	SERVIO_DEBUG=4 ./mdbserv

${APPNAME}: ${APPNAME}.o ${VLIBS} mdblogic.o

mdblogic.o: mdblogic.cpp  mdbserv.h

mdbserv.o: mdbserv.cpp mdbserv.h

clean:
	rm -f *~ *.o ${APPNAME} ${VLIBS} core

