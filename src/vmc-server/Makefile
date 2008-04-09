
APPNAME=vmcserv
include ../sodacom.in

all: ${APPNAME}

install: ${APPNAME}
	cp ${APPNAME} ${BIN}

${APPNAME}: ${APPNAME}.o ${VLIBS} vmccsd.o

clean:
	rm -f *~ *.o ${APPNAME} ${VLIBS} core

