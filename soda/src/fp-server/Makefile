
CPP=g++
CPPFLAGS=-g -I../lib

# I know, I know. In the current lack of a unified build system, use this hack.
LDFLAGS=-lfprint -lsqlite3 ../lib/servio.o

.SUFFIXES: .c .o

TARGET=fpserv

SRCS=fpserv_async.cpp fp_db.cpp fpserv.cpp
OBJS=$(SRCS:.cpp=.o)

all: ${TARGET}

#install: ${APPNAME}
#	cp ${APPNAME} ${BIN}

#run: all
#	DISPLAY=:0 XAUTHORITY=~kiosk/.Xauthority SERVIO_DEBUG=48 SERVIO_COMMDUMP=3 ./fpserv

.cpp.o:
	$(CPP) $(CPPFLAGS) -c $<  -o $@

${TARGET}: ${OBJS}
	$(CPP) $(CPPFLAGS) $(LDFLAGS) ${OBJS} -o ${TARGET}

install:
	cp ${TARGET} ${BIN}


clean:
	rm -f ${OBJS} ${TARGET}

