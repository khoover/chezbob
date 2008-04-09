#ifndef _SERCOM_H_
#define _SERCOM_H_



// OPEN flags
// group 1: mode (one must be present)
#define  SER_M8N1		0x0001	// 8 databits, no parity, 1 stop bit
#define  SER_M9N1		0x0002	// 9 databits, no parity, 1 stop bit
#define  SER_TCP		0x0003	// tcp/ip connection - port must be IP:port. NOT IMPLEMENTED 
// group 2: speed (one must be present for serial)
#define  SER_B300		(1 *0x100)	// 
#define  SER_B1200		(4 *0x100)	
#define  SER_B2400		(8 *0x100)	
#define  SER_B4800		(16*0x100)	
#define  SER_B9600		(32*0x100)	// 9600 baud speed
#define  SER_B19200		(64*0x100)	
#define  SER_B38400		(128*0x100)	
#define  SER_B57600		(192*0x100)	

// group 3: special flags
#define  SER_LOWLATENCY 	0x0010	// use ASYNC_LOW_LATENCY flag
#define  SER_SIGTIMEOUTS 	0x0020  // if prog recieves a signal while in ser_getc, timout occurs immediately

#define  SER_TIMEOUT	-2


typedef void* SER_HANDLE;

// open given port with given flags
// on error = NULL, and errno set
// otherwise, returns new SER_HANDLE
SER_HANDLE ser_open(char * port, int flags);

// non-blocking read of byte
// returns SER_TIMEOUT on timeout, -1 on error
//  or returns one character (8 or 9 bit)
// timeout is up to 'tm' milliseconds
int ser_getc(SER_HANDLE srh, int timeout);

// put the character back into the buffer
//  could be used on 8 or 9 bit chars
void ser_ungetc(SER_HANDLE srh, int c);

// send the bytes (blocking)
//  the bit9 variable sets the bit 9 for ALL outgoing bytes
// returns -1 on failure, or size on success
// bug: while write9 with bit9=1 is active, the bit9 on all incoming bits is flipped 
int ser_write9(SER_HANDLE srh, int bit9, char* bf, int size);

// send the bytes (blocking - does not return until data is sent)
// returns -1 on failure, or size on success
//  for 8 or less bit comm only
int ser_write(SER_HANDLE srh, char* bf, int size);

// close port, restore settings, frees the handle and related memry stucts
int ser_close(SER_HANDLE srh);

#endif
