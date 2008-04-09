APPNAME=MozKioskBin
include ../sodacom.in

all: ${APPNAME}

# location of the sodacom library...
SODAFW=/home/theamk/sodafw_dev/src


MOZ_SRC=/usr
MOZ_LIB=/usr/lib/firefox

#am I not getting something?
DINC=/usr/include/firefox
MOZ_INC=-I${DINC}/widget -I${DINC}/js -I${DINC}/string -I${DINC}/xpconnect -I${DINC}/layout -I${DINC}/pref -I${DINC}/dom -I${DINC}/xpcom -I${DINC}/gtkembedmoz

CXXFLAGS = -g `${MOZ_SRC}/bin/firefox-config --cflags`
LDFLAGS  += -Wl,-rpath-link,${MOZ_LIB} `${MOZ_SRC}/bin/firefox-config --libs xpcom nspr gfx` -l gtkembedmoz

CXXFLAGS +=  -I${SODAFW}/lib ${MOZ_INC} 
LDFLAGS  +=  ${SODAFW}/lib/servio.o

CXXFLAGS  += `pkg-config --cflags gtk+-x11-2.0`
LDFLAGS   += `pkg-config --libs gtk+-x11-2.0`

# print pathths of libs used..
#LDFLAGS   += -Wl,-t

MozKioskBin: TestGtkEmbed.o 
	g++  -o MozKioskBin TestGtkEmbed.o ${LDFLAGS} 

TestGtkEmbed.o: TestGtkEmbed.cpp 
	g++ -c TestGtkEmbed.cpp ${CXXFLAGS}

install: MozKioskBin
	cp MozKioskBin ${BIN}
	cp moz-kiosk ${BIN}

clean:
	@#make -C embed-intree clean
	rm -f *~ *.o core MozKioskBin linker.map

