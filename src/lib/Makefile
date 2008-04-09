
include ../sodacom.in

JFILES:=$(shell find com/theamk/ambus/ -name *.java)
JAVADOC=/usr/java/jdk1.5.0_05/bin/javadoc

all: ServIO.jar ${VLIBS} 

vlibs: ${VLIBS} 

${VLIBDIR}/sercom.o: sercom.cpp

${VLIBDIR}/servio.o: servio.cpp

docs:
	cp servio.h ${DOC_PATH}/servio.h.txt
	pod2html ServIO.pm > ${DOC_PATH}/ServIO.pm.html
	@#-quiet
	${JAVADOC} -d ${DOC_PATH}/ServIO-java -noqualifier "java.*" -link http://java.sun.com/j2se/1.5.0/docs/api com.theamk.ambus

install:
	cp ServIO.jar ${BIN}/../lib

ServIO.jar:  ${JFILES}
	javac  -source 1.4 ${JFILES}
	find com -name "*.class" | zip ServIO.jar -@

clean:
	find com -name "*.class" -exec rm {} \;
	rm -f *~ *.o ServIO.jar ${VLIBS}
