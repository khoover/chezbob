# $Id: makefile,v 1.1 2001-05-17 18:46:10 mcopenha Exp $
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

