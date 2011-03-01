#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <signal.h>
#include <errno.h>
#include <glob.h>

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

int MdbServ::report_fail(const char * where,
                         int code, 
                         std::string msg) {

    if (msg == "") {
        switch(code) {
        case 0:
            msg = "bad value";
            break;
        case -1:
            msg = "failed";
            break;
        case -2:
            msg = "timeout";
            break;
        default:
            msg = "unknown";
            break;
        }
    }

    std::string fullmsg = (boost::format("ERROR #%d in %s: %s")
                                    % code % where % msg.c_str()).str();

    sio_write(SIO_DEBUG|45, (char*)fullmsg.c_str());

    return (code<0)?code:-1;
};

bool strbegins(const char * slong, const char * sshort) {
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

void MdbBus::flush_buffer() {
  if (!srh) return;
  while (1) {
	int rv = ser_getc(srh, 0);
	if (rv<=0) return;
	sio_write(SIO_WARN, "junk in flush-buff: [%c] (0x%.2X)", (rv<32)?'?':rv, rv);
  };
};

const char * mdb_errcode[0x1F+1] = {
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



int MdbBus::send_command(const char * cmd, const char* expect, int timeout ) {

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
	return serv->report_fail("send_command.ser_write", 0);
  };

  int rv;

  // wait for command's ACK...
  rv = ser_getc(srh, timeout);
  if (rv != '\n')
      return serv->report_fail("send_command.ack", (rv<0)?rv:0, 
                               (boost::format("junk=0x%X cmd=[%s]")
                                             % ((rv>0)?rv:0)
                                             % cmd).str());

  // get actual response...
  bzero(resp_raw, sizeof(resp_raw));
  int rrsize = 0;
  while (rrsize < (sizeof(resp_raw)-4)) {
	int c = ser_getc(srh, timeout);
	if (c < 0) return serv->report_fail("send_command.ser_getc.2", c);
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
  sio_write(SIO_DEBUG | pollpri, "CMD\t[%s]=%s [%s]", cmd, (expect?expect:"*"), resp_raw);

  if (strbegins(resp_raw, "**")) {
	sio_write(SIO_WARN, "MDB board was powered up\t%s", resp_raw);
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
	  return serv->report_fail("send_command.asciitohex", hc, 
                                   (boost::format("char1=%.2X, char2=%.2X")
                                        % resp_raw[rrpos-2]
                                        % resp_raw[rrpos-1]).str()); // not a hex!
	};
	resp[resplen] = hc;
	resplen++;
  };

  if (resp[0] == 'X') {
	int i1 = resp[1];
	sio_write(SIO_WARN, "mdb error\t%d\t%s", 
                  i1, 
                  (((i1>=0) && (i1 < (sizeof(mdb_errcode)/sizeof(mdb_errcode[0])))) ?  mdb_errcode[i1] : "unknown")); 
	//if ((i1>=1) && (i1<=8)) cc_dtcount++;
	return -1;
  };

  if (expect) {
	if (strncmp(expect, (char*)resp, strlen(expect)) != 0) {
	  // nomatch
	  return serv->report_fail("send_command.bad_reply", 0,
                               (boost::format("cmd=[%s], need=[%s], get=[%s]")
                                    % cmd % expect % resp_raw).str());
	};
	memmove(resp, resp+strlen(expect), sizeof(resp)-strlen(expect));
  };

  return 1;
};






//
//
//                 MAIN
//
//

int main(int argc, char ** argv) {

  MdbServ mdbserv(argc, argv);
  
  
  signal(SIGHUP, &onsignal); 
  signal(SIGINT, &onsignal);
  signal(SIGTERM, &onsignal);
  signal(SIGPIPE, &onsignal);
  signal(SIGALRM, SIG_IGN); 
  signal(SIGUSR1, SIG_IGN); 
  signal(SIGUSR2, SIG_IGN); 


  int sleep_for = 0;
  while (!stop_num) {
        stop_num = mdbserv.sio_poll(sleep_for);
        if (stop_num != 0) break;

        stop_num = mdbserv.mdb_poll(sleep_for);
  };
  
  sio_close(stop_num, "Signal Recieved");
};
