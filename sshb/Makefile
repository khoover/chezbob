PROG = sshb

CC = gcc
CFLAGS = 
LIBS = 

SRCS = sshb.c
OBJS = $(SRCS:.c=.o)

.c.o:
	$(CC) -c $(CFLAGS) -o $@ $<

$(PROG): $(OBJS)
	$(CC) $(OBJS) $(LIBS) -o $@

clean:
	/bin/rm -f $(OBJS) $(PROG) core *~
