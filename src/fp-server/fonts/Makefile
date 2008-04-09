
 
all: font_browser


font_browser : font_browser.o  window.o
	g++ font_browser.o window.o -o font_browser `fltk-config --ldflags`

#                         -L/usr/lib -L/usr/X11R6/lib \
#                         -lfltk -lSM -lICE -lGLU -lGL \
#                          -lX11 -lXi -lXext -lXt -lXmu -ldl -lm

font_browser.o : font_browser.cxx window.h
	g++ -c -I/usr/include -I/usr/local/include font_browser.cxx -o font_browser.o

window.h window.o : window.fl
	fluid -c window.fl
	g++ -c -I/usr/local/include window.cxx -o window.o

clean:
	rm -f *.o font_browser window.{cxx,h}

