# (id tag removed to pacify cvs...may readd it later -as)
# template makefile for DIALOG sample 'install'
#
SHELL		= /bin/sh

prefix		= /usr/local
exec_prefix	= ${prefix}

srcdir		= .
top_builddir	= ../..

DESTDIR		=
bindir		= $(DESTDIR)${exec_prefix}/bin

CFLAGS		= -g -O2
CPPFLAGS	=  -DHAVE_CONFIG_H -I$(top_builddir) -I$(srcdir)/../.. -I. -I$(srcdir)
EXTRA_CFLAGS	= 
CC		= gcc
LDFLAGS		= 
LIBS		= -L../.. -ldialog -lncurses  -L/lib
RANLIB		= ranlib

RM		= rm -f

all: setup

setup: setup.o
	$(CC) -o $@ setup.o $(LIBS)

clean:
	rm -f *.o setup

test: setup
	./setup

