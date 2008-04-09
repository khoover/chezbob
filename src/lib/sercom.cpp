#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <strings.h>
#include <string.h>
#include <error.h>
#include <errno.h>
#include <limits.h>

#include <termios.h> 
#include <sys/time.h>
#include <sys/ioctl.h>
#include <sys/param.h>
//#include <asm/termios.h>
#include <unistd.h>
#include <linux/serial.h>


#ifndef CMSPAR
#define CMSPAR        010000000000   
#endif

//#define SER_BUSY_WAIT

#include "sercom.h"


//
//
//                     INTERNAL DECLARATIONS
//
//
typedef struct  {
  // orioginal flags to open 
  int flags;
  // file handle
  int fd;
  // originam termios structure
  struct termios old_term;
  // current termios
  struct termios new_term;
  // ungetc buffer. the value is -1 if empty
  int ungetc_bf[8];
  // buffer for data
  char b_data[64];
  int b_start; // index of last sent char
  int b_end; // index of last filled char + 1
} SerHandleImpl;


int ser_getc_8bit(SER_HANDLE srh, int timeout);
int ser_fail(char * func, int arg=0);


// prints error, returns -1
int ser_fail(char * func, int arg) {
	int e = errno;	
	fprintf(stderr, "serport: %s: %s (%d)\n", func, strerror(e), arg);
	return -1;
};


// tries to open into exiting srh
// if fails, returns -1 and srh is in the undefined mode (but must still be closed)
int ser_reopen(SER_HANDLE srh, char*port, int flags) {

  SerHandleImpl * ser = (SerHandleImpl*)srh;

  bzero(ser, sizeof(*ser));

  ser->flags = flags;
  
  ser->fd = open(port, O_RDWR | O_NOCTTY 
				| O_NONBLOCK
				);

  if (ser->fd == -1) {
	if (errno == EACCES) {
	  int x = errno;
	  fprintf(stderr, "PERMISSION DENIED to %s (uid=%d/%d, gid=%d/%d, groups ", port, getuid(), geteuid(), getgid(), getegid()); 
	  gid_t groups[NGROUPS];
	  int max = getgroups(sizeof(groups)/sizeof(gid_t), groups);
	  for (int i=0; i<max; i++)
		fprintf(stderr, "%s%d", i?", ":"", groups[i]);
	  fprintf(stderr, ")\n");
	  errno = x;
	};
	return ser_fail("open-port");
  };

  // save old port settings
  if (tcgetattr(ser->fd, &ser->old_term)==-1) {
	int fdo = ser->fd;
	close(ser->fd); ser->fd=-1; // close here to prevent restoring of wrong attrs
	return ser_fail("tcgetattr", fdo);
  };

  // set new sttings (raw mode)
  bzero(&ser->new_term, sizeof(ser->new_term));
  if (flags & SER_M9N1) {
	ser->new_term.c_iflag = PARMRK | INPCK;
	// CMSPAR makes parity 'stick' - PARODD set = SPACE, not set = MARK
	ser->new_term.c_cflag = CS8 | CREAD | CLOCAL | HUPCL | CMSPAR | PARENB;// | PARODD;
  } else if (flags & SER_M8N1) {
	ser->new_term.c_iflag = 0;
	ser->new_term.c_cflag = CS8 | CREAD | CLOCAL | HUPCL;
  } else {
	return ser_fail("serial-mode-set");
  };
  ser->new_term.c_oflag = 0;
  ser->new_term.c_lflag = 0;
  if  (flags & SER_B9600) {
	cfsetspeed(&ser->new_term, B9600);
  } else if  (flags & SER_B300) {
	cfsetspeed(&ser->new_term, B300);
  } else if  (flags & SER_B1200) {
	cfsetspeed(&ser->new_term, B1200);
  } else if  (flags & SER_B2400) {
	cfsetspeed(&ser->new_term, B2400);
  } else if  (flags & SER_B4800) {
	cfsetspeed(&ser->new_term, B4800);
  } else if  (flags & SER_B19200) {
	cfsetspeed(&ser->new_term, B19200);
  } else if  (flags & SER_B38400) {
	cfsetspeed(&ser->new_term, B38400);
  } else if  (flags & SER_B57600) {
	cfsetspeed(&ser->new_term, B57600);
  } else {
	return ser_fail("serial-speed-set");
  };
  if (tcsetattr(ser->fd, TCSAFLUSH, &ser->new_term)==-1) {
    return ser_fail("tcsetattr");
  };
		
  if (flags & SER_LOWLATENCY) {
	// stolen from setserial.c: set low latency
	// we do not reset it when exiting program. TODO: fix this
	struct serial_struct serinfo;
	if (ioctl(ser->fd, TIOCGSERIAL, &serinfo) < 0) {
	  perror("warning: TIOCGSERIAL failed");
	} else {
	  serinfo.flags |= ASYNC_LOW_LATENCY;
	  if (ioctl(ser->fd, TIOCSSERIAL, &serinfo) < 0) {
		perror("warning: TIOCCSSERIAL failed");
	  }
	};
  };
 
  ser->b_start = 0;
  ser->b_end = 0;
  for (int i=0; i<sizeof(ser->ungetc_bf)/sizeof(int); i++)
    ser->ungetc_bf[i]=-1;
  return 0;
};


SER_HANDLE ser_open(char*port, int flags) {

  SER_HANDLE srh  = (SER_HANDLE)malloc(sizeof(SerHandleImpl));

  if (ser_reopen(srh, port, flags)==-1) {
	int i = errno;
	ser_close(srh);
	free(srh);
	errno = i;
	return NULL;
  };

  return srh;
};


// get 8 bits - straight from the driver
int ser_getc_8bit(SER_HANDLE srh, int timeout) {
  SerHandleImpl * ser = (SerHandleImpl*)srh;
  if (timeout < 0) timeout = 0;
  ser->b_start++;
  int ecount = 0;
  if (ser->b_start >= ser->b_end) {
    // no data in the buffer
    ser->b_start = 0;
    while (1) {
      ser->b_end = read(ser->fd, ser->b_data, sizeof(ser->b_data));
      if (ser->b_end>0) break;
      
      if (errno == EAGAIN || ser->b_end == 0) {
	  // nothing
      } else if (errno == EINTR) {
	  return -2; // signal
      } else { 
          return ser_fail("serread-8");
      };
#ifndef SER_BUSY_WAIT
      if (ecount++ < 10) { // can handle up to 10 signal recieves
	fd_set fdr;
	struct timeval tv;
	tv.tv_sec = (timeout/1000);
	tv.tv_usec = (timeout%1000)*1000;
	FD_ZERO(&fdr);
	FD_SET(ser->fd, &fdr);
	int rv = select(ser->fd+1, &fdr, 0, 0, (timeout>=0)?&tv:0);
	if (rv<0) {
	  if (errno == EINTR) {
	    if (ser->flags & SER_SIGTIMEOUTS) {
	      return -2; // signal	
	    };
	  } else { 
	    return ser_fail("serread-emptpy"); 
	  };
	};
	if (rv == 0)
	  return -2;
      } else {
	return ser_fail("too-many-signals");
      };
#else
#error TIMEOUT NOT SUPPORTED
#endif
    };
  };

  return (unsigned char)ser->b_data[ser->b_start];
};

int ser_getc(SER_HANDLE srh, int timeout) {
  SerHandleImpl * ser = (SerHandleImpl*)srh;

  int rv;
  if (ser->ungetc_bf[0]!=-1) {
    rv = ser->ungetc_bf[0];
    memmove(&ser->ungetc_bf[0], 
			&ser->ungetc_bf[1],
			sizeof(ser->ungetc_bf)-sizeof(int));
  } else {
	if ((ser->flags & SER_M9N1)==0) 
	  return ser_getc_8bit(srh, timeout);

	// do 9-bit serial recieve/decode
    rv = ser_getc_8bit(ser, timeout);
    if (rv == 0xFF) {
      int r2 = ser_getc_8bit(ser, timeout);
      if (r2 == 0x00) {
		rv = ser_getc_8bit(ser, timeout);
		if (rv>=0) rv|=0x100;
      } else if (r2>=0) {
		if (rv != 0xFF)
		  ser_ungetc(ser, rv);
		rv = r2;
      };
    };
  };
  return rv;
};

void ser_ungetc(SER_HANDLE srh, int c) {
  SerHandleImpl * ser = (SerHandleImpl*)srh;
  
  for (int i=0; i<(sizeof(ser->ungetc_bf)/sizeof(int)-1); i++)
    if (ser->ungetc_bf[i]==-1) {
      ser->ungetc_bf[i] = c;
      return;
    };

  fprintf(stderr, "Error: ungetc buffer overflow\n");
  exit(14);
};


int ser_write(SER_HANDLE srh, char* bf, int size) {
  return ser_write9(srh, 0, bf, size);
};


int ser_write9(SER_HANDLE srh, int bit9, char* bf, int size) {
  SerHandleImpl * ser = (SerHandleImpl*)srh;

  if (size==0) return 0;

  if (bit9) {
    ser->new_term.c_cflag |= PARODD;
    if (tcsetattr(ser->fd, TCSADRAIN, &ser->new_term)==-1) {
      return ser_fail("tcsetattr-set");
    };
    tcdrain(ser->fd);
  };

  int left = size;
  int errcode = size;
  while (left > 0) {
    int dv = write(ser->fd, bf, left);
    if (dv < 0) {
      errcode = ser_fail("ser-write");
	  break;
    };
    left -= dv;
    bf += dv;
  };

  tcdrain(ser->fd);
  if (bit9) {
    ser->new_term.c_cflag &=~ PARODD;
    if (tcsetattr(ser->fd, TCSANOW, &ser->new_term)==-1) {
      return ser_fail("tcsetattr-unset"); 
    };
  };

  return errcode;
};


// close port, restore settings
int ser_close(SER_HANDLE srh) {
  SerHandleImpl * ser = (SerHandleImpl*)srh;

  if (ser->fd != -1) {
	tcsetattr(ser->fd, TCSAFLUSH, &ser->old_term);
	close(ser->fd);
  };
};
