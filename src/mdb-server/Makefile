APPNAME=mdbserv
include ../sodacom.in

all: ${APPNAME}

install: ${APPNAME}
	cp ${APPNAME} ${BIN}

run: all
	SERVIO_DEBUG=4 ./mdbserv

${APPNAME}: ${APPNAME}.o ${VLIBS} mdbmain.o mdbbus.o

mdbserv.o: mdbserv.cpp mdbserv.h

mdbbus.o: mdbbus.cpp mdbserv.h

mdbmain.o: mdbmain.cpp mdbserv.h

clean:
	rm -f *~ *.o ${APPNAME} ${VLIBS} core

