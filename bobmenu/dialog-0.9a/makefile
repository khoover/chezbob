# (id tag removed to pacify cvs...may try to readd it later -as)
# template makefile for DIALOG
#
SHELL		= /bin/sh

VERSION		= `cat VERSION`

prefix		= /usr/local
exec_prefix	= ${prefix}

srcdir		= .
top_builddir	= .

x		= 

DESTDIR		=
bindir		= $(DESTDIR)${exec_prefix}/bin
includedir	= $(DESTDIR)${prefix}/include
libdir		= $(DESTDIR)${exec_prefix}/lib
mandir		= $(DESTDIR)${prefix}/man
MANDIR		= $(mandir)/man1

# see po/makefile
localedir       = $(prefix)/share/locale

CFLAGS		= -g -O2
CPPFLAGS	=  -DHAVE_CONFIG_H -I. -I$(srcdir) -DLOCALEDIR=\"$(localedir)\" -DVERSION=\"$(VERSION)\"
EXTRA_CFLAGS	= 
CC		= gcc
LDFLAGS		= 
LIBS		= -lncurses  -L/lib # 
RANLIB		= ranlib

RM		= rm -f
LINT		= lint

INSTALL		= /usr/bin/install -c
INSTALL_PROGRAM	= ${INSTALL}
INSTALL_DATA	= ${INSTALL} -m 644

#
# Standard .c to .o compile line.
#
.c.o :
# compiling
	$(CC) $(CFLAGS) $(EXTRA_CFLAGS) $(CPPFLAGS) -c $<

EXTRAOBJS =  rc.o calendar.o fselect.o timebox.o guage.o tailbox.o
OBJS = $(EXTRAOBJS) \
	arrows.o \
	buttons.o \
	checklist.o \
	inputbox.o \
	inputstr.o \
	menubox.o \
	mouse.o \
	mousewget.o \
	msgbox.o \
	textbox.o \
	util.o \
	yesno.o

SRCS = $(OBJS:.o=.c)
HDRS = \
	colors.h \
	config.h \
	dialog.h

LIB	= libdialog.a
PROG	= dialog$x
ALL	= $(LIB) $(PROG)

BIN_DIRS	= $(bindir) $(MANDIR)
LIB_DIRS	= $(libdir) $(includedir)

all	:: $(ALL)

 :
	@echo "Building GNU gettext library..."
	@cd intl && $(MAKE) 

dialog.o \
$(OBJS) : $(srcdir)/dialog.h config.h

$(LIB) : $(OBJS)
	ar crv $(LIB) $(OBJS)
	$(RANLIB) $@

dialog$x : $(LIB) dialog.o # 
	$(CC) -o $@ dialog.o -L. -ldialog $(LDFLAGS) $(LIBS)

clean	::
#	@-test -f intl/Makefile && cd intl && $(MAKE)  $@
#	@-test -f po/Makefile && cd po && $(MAKE)  $@
	rm -f core *.o *~ tags TAGS $(ALL)

distclean :: clean
#	@-test -f intl/Makefile && cd intl && $(MAKE)  $@
#	@-test -f po/Makefile && cd po && $(MAKE)  $@
	rm -f intl/libintl.h intl/po2tbl.sed
	rm -f makefile config.h config.cache config.log config.status
	rm -f samples/install/makefile

install :: $(ALL) $(BIN_DIRS)
#	@-test -f intl/Makefile && cd intl && $(MAKE)  $@
#	@-test -f po/Makefile && cd po && $(MAKE)  $@
	$(INSTALL_PROGRAM) -s $(PROG) $(bindir)
	$(INSTALL_DATA) dialog.1 $(MANDIR)

uninstall ::
#	@-test -f intl/Makefile && cd intl && $(MAKE)  $@
#	@-test -f po/Makefile && cd po && $(MAKE)  $@
	rm -f $(bindir)/$(PROG)
	rm -f $(MANDIR)/dialog.1

# most users do not want/need the library, so the install rules are distinct.
install-lib :: $(LIB_DIRS)
	$(INSTALL_DATA) $(LIB) $(libdir)
	$(INSTALL_DATA) dialog.h $(includedir)

uninstall-lib :: $(LIB_DIRS)
	rm -f $(libdir)/$(LIB)
	rm -f $(includedir)/dialog.h

$(bindir) \
$(MANDIR) : ; $(srcdir)/mkdirs.sh $@

tags :
	ctags $(SRCS) $(HDRS)

TAGS :
	etags $(SRCS) $(HDRS)

lint:
	$(LINT) $(CPPFLAGS) *.c
