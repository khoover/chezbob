#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <signal.h>
#include <errno.h>
#include <glob.h>

#define MDBEXT
#include "sercom.h"
#include "servio.h"
#include "mdbserv.h"

//
//  P-115 interface required
//  DIP switch settings:
//      1 -  ON (cc present)
//      2 -  ON (bb present)
//      3 -  ON (200ms polling)
//      4 -  OFF (IMPORTANT!! no event mode)



//
//
//                    HOUSEKEEPING FUNCTIONS
//                     (network unrelated)
//   
//

static int max(int i1, int i2) {
 return (i1>i2)?i1: i2;
};

int stop_num = 0;

void onsignal(int num) { 
  stop_num = num;
};

int report_fail(char * where, int code, const char * msg, int i1, int i2, int i3) {
  if (msg==0) {
	msg = (code==0)?"bad value":
	  (code==-1)?"failed":
	  (code==-2)?"timeout":
	  "unknown";
  };
  char * msg1 = (char*)malloc(strlen(msg)+strlen(where)+64);
  sprintf(msg1, "ERROR #%d in %s: %s", code, where, msg);
  sio_write(SIO_DEBUG|45, msg1, i1, i2, i3);
  free(msg1);
  return (code<0)?code:-1;
};

bool strbegins(char * slong, char * sshort) {
  return strncmp(slong, sshort, strlen(sshort))==0;
};

int ascii_to_hex1(char c) {
  return 
	( (c>='0') && (c<='9') ) ? (c - '0') :
	( (c>='a') && (c<='f') ) ? (c - 'a' + 10) :
	( (c>='A') && (c<='F') ) ? (c - 'A' + 10) :
	-1;
};

int ascii_to_hex2(char * cc) {
  int i1 = ascii_to_hex1(cc[0]);
  int i2 = ascii_to_hex1(cc[1]);
  if ((i1==-1)||(i2==-1)) return -1;
  return (i1<<4) | i2;
};


//
//
//              COMM FUNCTIONS
//
//

void flush_buffer() {
  if (!srh) return;
  while (1) {
	int rv = ser_getc(srh, 0);
	if (rv<=0) return;
	sio_write(SIO_WARN, "junk in flush-buff: [%c] (0x%.2X)", (rv<32)?'?':rv, rv);
  };
};

char * mdb_errcode[0x1F+1] = {
  "unknown",
  "Dispense error",    // 01
  "Defective Tube Sensor",
  "No Credit",
  "Acceptor unplugged",
  "Tube Jam",
  "Changer ROM bad",
  "Coin routing error",
  "Coin Jam", // 08
  "undefined", "undefined", "undefined", "undefined", "undefined", "undefined", "undefined", // 09-0F
  "No bill in escrow", // 10
  "Defective Motor in Validator",
  "Sensor Problem",
  "Bill Validator bad ROM",
  "Bill validator jammed",
  "Cashbox out of position", // 15
  "undefined", "undefined", "undefined", "undefined", "undefined", // 16-1A
  "undefined", "undefined", "undefined", // 1B-1D
  "No Response", // 1E
  "MDB Checksum error" // 1F
};



int send_command(const char * cmd, char* expect, int timeout ) {

  if (srh == 0) 
	return -1;

  flush_buffer();

  // prepare buffer
  char bfout[256];
  strcpy(bfout, cmd);
  strcat(bfout, "\r");
  // send data
  errno = 0;
  if (ser_write(srh, bfout, strlen(bfout)) == -1) {
	sio_write(SIO_WARN, "serport gone: %d, scheduling reconnection", errno); 
	ser_close(srh);
	srh = 0;
	return report_fail("send_command.ser_write");
  };

  int rv;

  // wait for command's ACK...
  rv = ser_getc(srh, timeout);
  if (rv != '\n')  return report_fail("send_command.ack", (rv<0)?rv:0, "junk=0x%X cmd=[%s]", (rv>0)?rv:0, (int)cmd);

  // get actual response...
  bzero(resp_raw, sizeof(resp_raw));
  int rrsize = 0;
  while (rrsize < (sizeof(resp_raw)-4)) {
	int c = ser_getc(srh, timeout);
	if (c < 0) return report_fail("send_command.ser_getc.2", c);
	if (c=='\r') {  /// message done
	  break;
	};
	resp_raw[rrsize] = (c>=' ') ? c : '#';
	rrsize++;
  };
  resp_raw[rrsize] = 0;

  // log request and response...
  int pollpri = 10;
  if ( (cmd[0]=='P')  && (cmd[2]==0) && 
	   (resp_raw[0]=='Z') && (resp_raw[1]==0)) {
  	pollpri = 3; // uneventful device poll
  } else 
	if ( (strcmp(cmd, "T1")==0) || (strcmp(cmd, "T2")==0) || (strcmp(cmd, "Q")==0) ) {
	  pollpri = 7; // keepalive polls
  };
  sio_write(SIO_DEBUG | pollpri, "CMD\t[%s]=%s [%s]", (int)cmd, (int)(expect?expect:"*"), (int)resp_raw);

  if (strbegins(resp_raw, "**")) {
	sio_write(SIO_WARN, "MDB board was powered up\t%s", (int)resp_raw);
	cc_ready = 0;
	bb_ready = 0;
	return -1;
  };

  // fill non-hex part of response code
  int rrpos = 1;
  resplen = 1;
  bzero(resp, sizeof(resp));
  resp[0] = resp_raw[0];

  if (strchr("PQIST", resp[0])) {
	while ((rrpos<rrsize) && (resp_raw[rrpos]==' ')) rrpos++;
	resp[resplen] = resp_raw[rrpos]; rrpos++; resplen++;
  };

  // now read the hex characters...
  // no need to check for EOLn often, as there will be 4 binary 0's after the data end
  while (rrpos < rrsize) {
	while (resp_raw[rrpos]==' ') rrpos++;  // skip spaces between chars
	if (resp_raw[rrpos]==0) break;
	int hc = ascii_to_hex2(resp_raw + rrpos); rrpos+=2;
	if (hc==-1) {
	  return report_fail("send_command.asciitohex", hc, "char1=%.2X, char2=%.2X", 
						 resp_raw[rrpos-2], resp_raw[rrpos-1]);; // not a hex!
	};
	resp[resplen] = hc;
	resplen++;
  };

  if (resp[0] == 'X') {
	int i1 = resp[1];
	sio_write(SIO_WARN, "mdb error\t%d\t%s", i1, (int) (((i1>=0) && (i1 < (sizeof(mdb_errcode)/sizeof(mdb_errcode[0])))) ?
			  mdb_errcode[i1] : "unknown")); 
	//if ((i1>=1) && (i1<=8)) cc_dtcount++;
	return -1;
  };

  if (expect) {
	if (strncmp(expect, (char*)resp, strlen(expect)) != 0) {
	  // nomatch
	  return report_fail("send_command.bad_reply", 0, "cmd=[%s], need=[%s], get=[%s]",
						 (int)cmd, (int)expect, (int)resp_raw);
	};
	memmove(resp, resp+strlen(expect), sizeof(resp)-strlen(expect));
  };

  return 1;
};




char * ser_port; 

bool open_serport() {
  errno = 0;
  char real_port[1512];
  
  glob_t gl;
  bzero(&gl, sizeof(gl));
  int gt = glob(ser_port, GLOB_ERR|GLOB_MARK|GLOB_NOCHECK, 0, &gl);
  if ((gt != 0) || (gl.gl_pathc == 0)) {
	sio_write(SIO_WARN, "glob %s: retval %d, results %d", ser_port, errno); 
	strncpy(real_port, ser_port, sizeof(real_port));
  } else if (gl.gl_pathc == 1) {
	strncpy(real_port, gl.gl_pathv[0], sizeof(real_port));
  } else {
	strncpy(real_port, gl.gl_pathv[gl.gl_pathc - 1], sizeof(real_port));
	sio_write(SIO_LOG, "glob %s: %d results, picking %s, first 3: %s/%s/%s",
			  ser_port, gl.gl_pathc, 
			  real_port,
			  (gl.gl_pathc>=1)?gl.gl_pathv[0] : "{null}",
			  (gl.gl_pathc>=2)?gl.gl_pathv[1] : "{null}",
			  (gl.gl_pathc>=3)?gl.gl_pathv[2] : "{null}");
  };

  srh = ser_open(real_port, SER_M8N1 | SER_B9600 | SER_SIGTIMEOUTS); 
  if (!srh) {
	sio_write(SIO_WARN, "could not open port at %s (actual %s): %d", ser_port, real_port, errno); 
	return false;
  } else {
	sio_write(SIO_LOG, "opended serport at %s (actual %s)", ser_port, real_port); 
  };
  return true;
};


//
//
//                 MAIN
//
//

int main(int argc, char ** argv) {

  char cmd[1024];
  char * cmdv[16];
  int cmdc;
  int cmdlen;

  
  if (sio_open(argc, argv, "MDBSERV", VERSION, "") < 0) {
	exit(11);
  };

  ser_port = strdup("/dev/ttyUSB0");
  sio_getvar("port", "D:s", &ser_port);
  if (!open_serport()) {
	while (sio_read(cmd, sizeof(cmd), 100) > 0) {};
	sio_close(2, "serial port open failed");
    exit(2);
  };


  sio_write(SIO_DATA, "SYS-ACCEPT\tCASH-\tSYS-SET");
  
  signal(SIGHUP, &onsignal); 
  signal(SIGINT, &onsignal);
  signal(SIGTERM, &onsignal);
  signal(SIGPIPE, &onsignal);
  signal(SIGALRM, SIG_IGN); 
  signal(SIGUSR1, SIG_IGN); 
  signal(SIGUSR2, SIG_IGN); 

  esc_total = 0;
  esc_bill = 0;
  bzero(esc_coins, sizeof(esc_coins));
  cc_ready = 0;
  bb_ready = 0;
  escrow_change("reset", 0, 0);
  want_enabled = 0;

  sio_getvar("enabled", "D+:d", &want_enabled);

  bool last_ready = false; // last 'ready' state

  int sleep_for = 0;
  int next_scan = 0; // when to rescan tube/bill acceptor status
  while (!stop_num) {

	flush_buffer();

	errno = 0;
	if ((cmdlen=sio_read(cmd,sizeof(cmd),sleep_for))>0) {
	  cmdc = sio_parse(cmd, cmdv, sizeof(cmdv));
	  if (strncmp(cmdv[0], "CASH-", 5) == 0) {
	    sio_write(SIO_DEBUG|15, "DO-COMMAND\t%s", cmd);
	  };

	  if (strcmp(cmdv[0], "CASH-RESET")==0) {
		cash_reset();
	  } else if (strcmp(cmdv[0], "CASH-ACCEPT")==0) {
		int amt = 0;
		if ((cmdc>1)) amt = atoi(cmdv[1]);
		cash_accept(1);
		if (esc_total) {
		  sio_write(SIO_DATA, "CASH-FAIL\t%d", esc_total);
		} else {
		  sio_write(SIO_DATA, "CASH-OK");
		};
	  } else if (strcmp(cmdv[0], "CASH-REJECT")==0) {
		cash_accept(0);
		if (esc_total) {
		  sio_write(SIO_DATA, "CASH-FAIL\t%d", esc_total);
		} else {
		  sio_write(SIO_DATA, "CASH-OK");
		};
	  } else if (strcmp(cmdv[0], "CASH-STATUS")==0) {
		cc_tube_refresh(1);
		bb_stacker_refresh(1);
		sio_write(SIO_DATA, "CASH-ESCROW\t%d\t%d\t%d", esc_total, 0, 0);
		last_ready = !last_ready;
	  } else if ((strcmp(cmdv[0], "CASH-CHANGE-MAN")==0) && (cmdc==3)) {
		int denom = atoi(cmdv[1]);
		int count = atoi(cmdv[2]);

		int type = -1;
		for (int i=0; i<16; i++)
		  if ((cc_values[i] == denom) && (cc_count[i]>=count)) {
			type = i;
			break;
		  };

		int rv = -1;
		if (type > -1) rv = giveout_coins(type, count);
		if (rv != count) {
		  report_fail("cash-change-man.giveout", rv, "type=%d cnt=%d rv=%d", type, count, rv);
		  sio_write(SIO_DATA, "CASH-FAIL\t%d", max(rv,0)*denom);
		} else {
		  sio_write(SIO_DATA, "CASH-OK");
		};	
	  } else if ((strcmp(cmdv[0], "CASH-CHANGE")==0) && (cmdc==2)) {
		int amount = atoi(cmdv[1]);
		int rv = giveout_smart(amount);
		if (rv != amount) {
		  report_fail("cash-change.giveout-smart", rv, "req=%d", amount);
		  sio_write(SIO_DATA, "CASH-FAIL\t%d", max(0, rv));
		} else {
		  sio_write(SIO_DATA, "CASH-OK");
		};	
	  } else if ((strcmp(cmdv[0], "CASH-MANUAL-DISP")==0) && (cmdc==3)) {
		int denom = atoi(cmdv[1]);
		int mode = atoi(cmdv[2]);

		for (int i=0; i<16; i++)
		  if ((denom==0) || (cc_values[i] == denom)) {
			cc_mandisp[i] = mode;
		  };
		cc_tube_refresh(0);
		sio_write(SIO_DATA, "CASH-OK");
	  } else if (strncmp(cmdv[0], "CASH-", 5)==0) {
		sio_write(SIO_DEBUG, "unparseable CASH- command\t%s\t%s\t%s",
				  (int)(cmdv[0]?cmdv[0]:"{null}"),
				  (int)(cmdv[1]?cmdv[1]:"{null}"),
				  (int)(cmdv[2]?cmdv[2]:"{null}"));
	  };
	};
	if (cmdlen == -1) {
	  // server died
	  stop_num = errno + 1000;
	  break;
	};

	

	sleep_for = 200; // default poll is 0.2 sec

	if (!srh) {
	  // no serial port...
	  cc_ready = 0;
	  bb_ready = 0;
	  open_serport();
	  sleep_for = 3000;
	} else if (!cc_ready) {
	  // coinchanger not ready? init it
	  if (cc_init() < 0) {
		sleep_for = 3000; // sleep 3 sec, retry coinchanger
	  };
	} else if (!bb_ready) {
	  // bill acceptor not ready? init it, too
	  if (bb_init() < 0) {
		sleep_for = 3000; // sleep 3 sec, retry bill acceptor
	  };
	} else {
	  // manually poll the device
	  if (cc_ready > 0) 
		if (cc_poll() < 0) next_scan = 0;
	  if (bb_ready > 0) 
		if (bb_poll() < 0) next_scan = 0;

	  if (time(0) > next_scan) {
		int rv = cc_tube_refresh(0);
		if (rv < 0) rv = cc_tube_refresh(0); // retry if first time failed
		if (rv < 0) 
		  cc_ready = 0; // coinchanger went offline
		
		rv = bb_stacker_refresh(0);
		if (rv < 0) rv =  bb_stacker_refresh(0);
		if (rv < 0) 
		  bb_ready = 0; // stacker went offline

		next_scan = time(0) + 10; // re-check in 10 seconds
	  };
	};

	bool ready = ((cc_ready > 0) && (bb_ready > 0));
	sio_setvar("ready",    "+:d", ready);
	sio_setvar("cc_ready", "+:d", cc_ready);
	sio_setvar("bb_ready", "+:d", bb_ready);
  };
  cash_reset(); // return stuff in escrow
  
  if (srh)
	ser_close(srh);
  sio_close(stop_num, "Signal Recieved");
};
