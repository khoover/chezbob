APPNAME=sndserv
include ../sodacom.in

all: ${APPNAME}

install: ${APPNAME}
	cp ${APPNAME} ${BIN}

run: all
	SERVIO_DEBUG=4 ./sndserv

${APPNAME}: ${APPNAME}.o ${VLIBS} sndmain.o

sndserv.o: sndserv.cpp sndserv.h
sndmain.o: sndmain.cpp sndserv.h

clean:
	rm -f *~ *.o ${APPNAME} ${VLIBS} core

