include ../sodacom.in

all: test1.class

run: test1.class
	time java -cp ${VLIBDIR}:. test1

lib:
	make -C ../lib

test1.class: test1.java
	javac -cp ${VLIBDIR} test1.java

clean:
	rm -f *~ *.class
