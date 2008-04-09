
APPNAME=fpserv
include ../sodacom.in

LIBVFINGER=../../libs/VFinger

#FPREADER=fps200
FPREADER=dpfp

LINK.o   +=  -L${LIBVFINGER} -lVFinger  -lusb `fltk-config --ldflags --use-images`  `mysql_config --libs` -g ${LDFLAGS}
CPPFLAGS +=  -I${LIBVFINGER} -pthread ` fltk-config  --cxxflags --use-images`

ifeq (${FPREADER}, fps200)
FPALL_ROOT=/home/theamk/fingers
LIBFPS=${FPALL_ROOT}/fps200ul
CPPFLAGS += -I${LIBFPS}/include -DREADER_FPS200
LDFLAGS += ${LIBFPS}/libfps.a
else
ifeq (${FPREADER}, dpfp)
CPPFLAGS += $(shell pkg-config libdpfp --cflags) -DREADER_DPFP
LDFLAGS += $(shell pkg-config libdpfp --libs)
else
$(error invalid FPREADER value)
endif
endif


all: ${APPNAME}

install: ${APPNAME}
	cp ${APPNAME} ${BIN}

run: all
	DISPLAY=:0 XAUTHORITY=~kiosk/.Xauthority SERVIO_DEBUG=48 SERVIO_COMMDUMP=3 ./fpserv

${APPNAME}: ${APPNAME}.o fp_db.o fp_reader.o ${VLIBS} 

fpserv.o: fpserv.cpp 

fp_db.o: fp_db.cpp

fp_reader.o: fp_reader.cpp

others:
	make -C ${LIBFPS} clean all

# test
clean:
	rm -f *~ *.o ${APPNAME} ${VLIBS} core

