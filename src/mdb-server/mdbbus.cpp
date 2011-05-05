#include "mdbserv.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <signal.h>

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



bool MdbBus::open_serport() {
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

int MdbBus::poll(int &sleep_for)
{
    int stop_num = 0;

    sleep_for = 200; // default poll is 0.2 sec

    if (!srh) {
      // no serial port...
      cc_ready = 0;
      bb_ready = 0;
      open_serport();
      sleep_for = 3000;
    } else {
        flush_buffer();

        /* Check for data */
        if (!cc_ready) {
            // coinchanger not ready? init it
            if (cc_init() < 0) {
                sleep_for = 3000; // sleep 3 sec, retry coinchanger
            }
        } else if (!bb_ready) {
            // bill acceptor not ready? init it, too
            if (bb_init() < 0) {
                sleep_for = 3000; // sleep 3 sec, retry bill acceptor
            }
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
            }
        }
    }

    bool ready = ((cc_ready > 0) && (bb_ready > 0));
    sio_setvar("ready",    "+:d", ready);
    sio_setvar("cc_ready", "+:d", cc_ready);
    sio_setvar("bb_ready", "+:d", bb_ready);

    return stop_num;
}

void MdbBus::flush_buffer() {
  if (!srh) return;
  while (1) {
	int rv = ser_getc(srh, 0);
	if (rv<=0) return;
	sio_write(SIO_WARN, "junk in flush-buff: [%c] (0x%.2X)", (rv<32)?'?':rv, rv);
  };
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

int MdbBus::cc_poll() {
  int ev_cnt = 0;
  while (send_command("P1") >= 0) {
	if (resp[0] == 'Z') {
	  return ev_cnt;

	} else if ((resp[0] == 'P') && (resp[1] == '1')) {
	  int i1 = resp[2];
	  sio_write(SIO_LOG, "accepted coin\t%d\t%d", i1, cc_values[i1]); 
	  if ((i1<0)||(i1>15)) i1 = 15;
          serv->update_coin_escrow(i1, 1);
	  cc_tube_refresh(0);
	  serv->escrow_change("deposit", i1+200, cc_values[i1]);
	} else if ((resp[0] == 'P') && (resp[1] == '2')) {
	  sio_write(SIO_LOG, "rejected bad coin\t%d\t%d", resp[2], cc_values[resp[2]]); 

	} else if ((resp[0] == 'P') && (resp[1] == '3')) {
	  sio_write(SIO_LOG, "manually dispensed coin\t%d\t%d\t%d", resp[2], cc_values[resp[2]], resp[3]); 
	  cc_tube_refresh(0);

	} else if (resp[0] == 'W') {
	  sio_write(SIO_DATA, "CASH-RETURN");

	} else if (resp[0] == 'G') {
	  // manual dispanse - ignore

	} else {
	  sio_write(SIO_WARN, "unknown CC poll response: %s", resp_raw);
	};
	ev_cnt++;
  };
  return -1;
};

int MdbBus::cc_tube_refresh(int forceprint) {
  char bf[512];

  int grv  = 0;

  if (cc_ready > 0) {

	// get full status
	if (send_command("T1", "T1") < 0) return -1;
	for (int i=0; i<16; i++) 
	  if (cc_values[i]) {
		cc_full[i] = (((resp[1 - i/8] >> (i%8)) & 1) != 0);
	  } else cc_full[i] = 0;
  
	// get coin tube counts
	if (send_command("T2", "T2") < 0) return -1;
	int man_ok = 0;
	for (int i=0; i<16; i++) 
	  if (cc_values[i]) {
		cc_count[i] = resp[i];
		//	 check for manual dispense
		if ( (cc_mandisp[i]==0) || 
			 ((cc_mandisp[i] != -1) && (cc_mandisp[i] < cc_count[i])) )
		  man_ok |= (1<<i);
		sio_setvar("coins%", "i+:ddddd", i, cc_values[i], cc_full[i], cc_count[i], (man_ok&(1<<i))?1:0, cc_mandisp[i]);
	  } else {
		cc_count[i] = 0;
	  };

	if (cc_man_ok != man_ok) {
	  cc_man_ok = man_ok;
	  sprintf(bf, "M %.4X", man_ok);
	  if (send_command(bf, "Z") < 0)
		serv->report_fail("tube_refresh.set_manok");
	  send_command("E1", "Z"); // enable coin acceptance to action settings
	  if (cc_ready != 2) 
		if (send_command("D1", "Z") < 0) { // disable aceptance back if needed
		  sleep(1); send_command("D1", "Z");
		  serv->report_fail("tube_refresh.set_manok.cleanup");	 
		};
	};

	if ((cc_ready == 1) && (want_enabled & 5)) {
	  // enable coin acceptance	
	  int rv = send_command("E1", "Z");
	  if (rv < 0) grv=serv->report_fail("cash_enable.enable-coin-acceptance", rv);
	  else cc_ready = 2;
	};
	if ((cc_ready == 2) && !(want_enabled & 5)) {
	  // disable coin acceptance	
	  int rv = send_command("D1", "Z");
	  if (rv < 0) grv=serv->report_fail("cash_enable.disable-coin-acceptance", rv);
	  else cc_ready = 1;
	};
  };

  // just in case...
  serv->set_escrow_variables();
  sio_setvar("cc_ready", "+:d", cc_ready);

  return 0;
};


int MdbBus::cc_init() {
  char bf[512]; // 16 ctypes => 32 chars per cointype

  cc_ready = 0;
  // reset changegiver, disable acceptance
  if (send_command("R1", "Z", MdbBus::RESET_TIMEOUT) < 0) return -1;

  if (send_command("P1", "I1") < 0) return -1; // space is stripped

  // get scaling
  if (send_command("S2", "S2") < 0) return -1;
  int sfactor = resp[0];
  sio_write(SIO_DEBUG, "CC: scaling factor %d, decimal point %d", resp[0], resp[1]);

  // get misc values
  if (send_command("S4", "S4") < 0) return -1;
  sio_write(SIO_DEBUG, "CC: feature level %d, country code %.4X", resp[0], resp[2] ||  (resp[1]<<8));

  // get coin cost
  if (send_command("S1", "S1") < 0) return -1;
  bf[0] = 0;
  bzero(cc_values, sizeof(cc_values));
  for (int i=0; i<16; i++) 
	if (resp[i] != 0) {
	  cc_values[i] = resp[i] * sfactor;
	  if (bf[0]) strcat(bf, ", ");
	  sprintf(strchr(bf, 0), "#%d=%d", i, cc_values[i]);
	};
  sio_write(SIO_DEBUG, "CC: coin values: %s", bf);

  // get routing
  if (send_command("S3", "S3") < 0) return -1;
  bf[0] = 0;
  for (int i=0; i<16; i++) 
	if (((resp[1 - i/8] >> (i%8)) & 1) != 0) {
	  if (bf[0]) strcat(bf, ", ");
	  sprintf(strchr(bf, 0), "#%d", i);
	};
  sio_write(SIO_DEBUG, "CC: routed to tube: %s", bf);

  for (int i=0; i<16; i++)
	cc_mandisp[i] = -1; // disable manual dispense
  cc_man_ok = -1;

  // accept all coins
  if (send_command("N FFFF", "Z") < 0) return -1;
  // no manual dispense
  if (send_command("M 0000", "Z") < 0) return -1;

  cc_ready = 1;
  if (cc_tube_refresh(1) < 0) {
	return -1;
  };

  return 0;
};




//
//
//                     CASH CHANGER - GIVEOUT
//
//
int MdbBus::giveout_coins(int type, int count) {
  int rv, grv=0;

  // fail if coinchnager not ready
  if (cc_ready < 1) return -1;
  // disable coin acceptance
  send_command("D1", "Z"); 

  int done = 0;
  while (done < count) {
	// check for the coin counts
	cc_tube_refresh(-1);
	// we give out all coins at once if there is enough
	//    if not, we try anyway with only 1 coin
	int ctry = (cc_count[type] > (count-done)) ? (count-done) : 
	  cc_count[type]; // ? cc_count[type] : 1;

	if (ctry > 8) ctry = 8;
	if (ctry <= 0) break; // cannot vend when tube is empty - can fail w/o error message
	// give the command
	sio_write(SIO_DEBUG, "CC: trying to give out %d coins of type #%d (%d), done %d/%d", 
		  ctry, type, cc_values[type], done, count);

	char bf[64];
	sprintf(bf, "G %.2X %.2X", type, ctry);
	rv = send_command(bf, "Z", MdbBus::GIVEOUT_TIMEOUT); 
	if (rv < 0) grv = serv->report_fail("giveout_coins.giveout", rv);
	// poll every 100ms up to 10 sec, until results are ready
	for (int i=0; i<100; i++) {
	  rv = send_command("P1"); // poll until OK
	  if (rv<0) { grv = serv->report_fail("giveout_coins.pollfail", rv); break; };
	  if (resp[0] == 'Z')  break; // got our response 
	  if (resp[0] != 'G') {
		grv = serv->report_fail("giveout_coins.pollfail", 0,
                        (boost::format("invalid data: %s") % resp_raw).str());
                break;
	  };
	  usleep(100*1000);
	};
	
	if (grv != 0) {
	  // failed
	  break;
	} else {
	  done += ctry;
	  sleep(1);
	};
  };

  if (cc_ready == 2) {
	rv = send_command("E1", "Z"); // re-enable coin acceptance	
	if (rv < 0) grv = serv->report_fail("giveout_coins.reenable", rv);
  };
  
  // update escrow
  if (done) {
	int diff = cc_values[done]*done;
	if (diff> serv->get_escrow_total())
            diff = serv->get_escrow_total();
        serv->escrow_change("return", type+200, -diff);

        serv->update_coin_escrow(type, -done);

	if (serv->get_coin_escrow(type) < 0) 
            serv->reset_coin_escrow(type);
  };

  cc_tube_refresh(0);

  return done ? done : grv;
};

int MdbBus::giveout_smart(int amount) {
  // we assume that coins are going to be in the increasing denominations
  cc_tube_refresh(-1);
  int todo = amount;
  for (int i=15; i>=0; i--) 
	if (cc_values[i] && cc_count[i])
	  {
		int req = todo / cc_values[i];
		int act = giveout_coins(i, req);
		if (act > 0) {
		  todo -= act*cc_values[i];
		};
		if (todo <= 0) break;
	  };
  return amount-todo;
};


int MdbBus::bb_poll() {
  int res = 0;
  while (send_command("P2") >= 0) {
	int i1 = resp[2];

	if (resp[0] == 'Z') {
	  return res;
        }

	if ((resp[0] == 'Q') && (resp[1] == '1')) {
          res = 1;

	  sio_write(SIO_LOG, "accepted bill\t%d\t%d", i1, bb_values[i1]); 
	  if ((i1<0)||(i1>15)) i1 = 15;

	  if (serv->get_bill_escrow() != 0) {
	    sio_write(SIO_ERROR,
                      "DOUBLE accept message - had %d, got %d, ignoring",
                      serv->get_bill_escrow(),
                      100+i1);
	  } else {
              serv->update_bill_escrow(100+i1);
              bb_stacker_refresh(0);
              serv->escrow_change("deposit",
                                  serv->get_bill_escrow(),
                                  bb_values[i1]);
	  };

	} else if ((resp[0] == 'Q') && (resp[1] == '2')) {
          res = 2;
	  sio_write(SIO_LOG, "stacked bill\t%d\t%d", i1, bb_values[i1]); 
	  if ((i1+100) != serv->get_bill_escrow()) {
		sio_write(SIO_ERROR,
                          "MISMATCH between accept and stack: accept %d, stack %d",
                          serv->get_bill_escrow(),
                          i1+100);
		// we will use whatever is stored
	  };
	  int val = 0;
	  if (serv->get_bill_escrow()) {
		val = -bb_values[serv->get_bill_escrow()-100];
		serv->escrow_change("accept", serv->get_bill_escrow(), val);
	  };
	  sio_write(SIO_DATA, "CASH-DEPOSIT\t%d\t%d", -val, 100+i1);
          serv->reset_bill_escrow();
	  bb_stacker_refresh(0);

	} else if ((resp[0] == 'Q') && (resp[1] == '3')) {
          res = 3;
	  sio_write(SIO_LOG, "returned bill\t%d\t%d", i1, bb_values[i1]); 
	  if ((i1+100) != serv->get_bill_escrow()) {
		sio_write(SIO_ERROR,
                          "MISMATCH between accept and return: accept %d, stack %d",
                          serv->get_bill_escrow(), i1+100);
	  };
	  if (serv->get_bill_escrow()) {
		serv->escrow_change("stack",
                              serv->get_bill_escrow(),
                              -bb_values[serv->get_bill_escrow()-100]);
	  };
          serv->reset_bill_escrow();
	  bb_stacker_refresh(0);
	  
	} else if ((resp[0] == 'Q') && (resp[1] == '4')) {
          res = 4;
	  sio_write(SIO_LOG, "rejected bill\t%d\t%d", i1, bb_values[i1]); 
	  if (serv->get_bill_escrow()) {
	    sio_write(SIO_ERROR, "Got REJECT while having bill %d in escrow", 
                      serv->get_bill_escrow());
	  };
          serv->reset_bill_escrow();
	  bb_stacker_refresh(0);

	} else {
	  sio_write(SIO_WARN, "unknown BB poll response: %s", resp_raw);
	};
  };
  return -1;
};

int MdbBus::bb_stacker_refresh(int forceprint) {

  int grv = 0;

  if (bb_ready > 0) {

	// get stacker info
	if (send_command("Q", "Q") < 0) return -1;  
	//if ( bb_full != (resp[0] != 'N') ) print = 1;
	bb_full = resp[0] != 'N';
	bb_stacked = (resp[1]<<8) | resp[2];

	// activate if needed
	if ((bb_ready==1) && (want_enabled & 3)) {
	  int rv = send_command("E2", "Z");
	  if (rv < 0) grv=serv->report_fail("cash_enable.enable-bill-acceptance", rv);
	  else bb_ready = 2;
	};
	// deactivate is needed
	if ((bb_ready==2) && (!(want_enabled & 3))) {
	  int rv = send_command("D2", "Z");
	  if (rv < 0) grv=serv->report_fail("cash_enable.disable-bill-acceptance", rv);
	  else bb_ready = 1;
	};

  };

  // send variables
  serv->set_escrow_variables();
  sio_setvar("bb_ready",    "+:d", bb_ready);
  sio_setvar("bb_full",     "+:d", bb_full);
  sio_setvar("bb_count",    "+:d", bb_stacked);


  return 0;

};

int MdbBus::bb_init() {

  char bf[512]; // 16 ctypes => 32 chars per cointype

  bb_ready = 0;
  // reset, disable acceptance
  if (send_command("R2", "Z", MdbBus::RESET_TIMEOUT) < 0) return -1;

  // ensure its connected
  if (send_command("P2", "I2") < 0) return -1;

  // get scaling
  if (send_command("S6", "S6") < 0) return -1;
  int sfactor = resp[1] | (resp[0]<<8);
  sio_write(SIO_DEBUG, "BB: scaling factor %d, decimal point %d", sfactor, resp[2]);

  // get misc values
  if (send_command("S8", "S8") < 0) return -1;
  sio_write(SIO_DEBUG, "BB: feature level %d, country code %.4X, hi-security on %.4X", 
			resp[0], resp[2] ||  (resp[1]<<8), resp[4] || (resp[3]<<8));

  if (send_command("S7", "S7") < 0) return -1;
  bb_capacity = resp[2] | (resp[1]<<8);
  sio_write(SIO_DEBUG, "BB: escrow=%d, capacity=%d", (int)(char)resp[0], bb_capacity); 

  // get values
  if (send_command("S5", "S5") < 0) return -1;
  bf[0] = 0;
  bzero(bb_values, sizeof(bb_values));
  for (int i=0; i<16; i++) 
	if (resp[i] != 0) {
	  bb_values[i] = resp[i] * sfactor;
	  if (bf[0]) strcat(bf, ", ");
	  sprintf(strchr(bf, 0), "#%d=%d", i, bb_values[i]);
	  sio_setvar("bills%", "i:d", i, bb_values[i]);
	};
  sio_write(SIO_DEBUG, "BB: bill values: %s", bf);

  // accept all bills
  if (send_command("L FFFF", "Z") < 0) return -1;
  // escrow all bills
  if (send_command("J FFFF", "Z") < 0) return -1;

  // set low security on all bits
  if (send_command("V 0000", "Z") < 0) return -1;

  bb_ready = 1;

  // refresh stacker status
  if (bb_stacker_refresh(1) < 0) return -1;

  return 0;
};


//
//
//                    CASH (BB+CC) GENERAL
//
//
void MdbBus::cash_reset() {
  int rv;
  // disable acceptance
  // TODO??

  if (rv < 0) serv->report_fail("cash_reset.cash-disable", rv);
  // return stuff in escrow
  rv = cash_accept(0);
  if (rv < 0) serv->report_fail("cash_reset.escrow-reject", rv);
  // request devices reset
  cc_ready = 0;
  bb_ready = 0;
};

// accept/reject stuff in escrow
int MdbBus::cash_accept(bool accept, int amt) {
  int grv = 0;

  if (accept && (amt != 0)) {
	return serv->report_fail("non-zero amounts unsuported", amt);
  };

  //
  //    get rid of BILL
  //
  if (serv->get_bill_escrow()) {
	const char * cmd = accept ? "K1": "K2";

	if ((!accept) && (bb_values[serv->get_bill_escrow()-100] > serv->get_escrow_total())) {
	  // do not return bill if the money was returned by some other means (coins)
	  sio_write(SIO_ERROR,
                    "not returning bill #%d (value %d), as escrow has %d",
                    serv->get_bill_escrow(),
                    bb_values[serv->get_bill_escrow()-100],
                    serv->get_escrow_total());
	  // accept it instead...
	  cmd = "K1";
	};

        /* This isn't in the docs.
	send_command("D2", "Z"); // disable bill acceptance
         */
	
	int rv = send_command(cmd, "Z", MdbBus::BILL_ACCEPT_TIMEOUT);
	if (rv < 0) grv = serv->report_fail("cash_accept.bill.reject", rv);
	for (int i=0; i<10*5; i++) { // wait up to 10 seconds for bill to be ejected
	  // poll bill acceptor until message handler clears esc_bill
	  rv = bb_poll();
	  if (rv < 0) grv = serv->report_fail("cash_accept.bill.poll", rv);
          /* Double accept, re-issue command */
          else if (rv == 1)
          {
                int nrv = send_command(cmd, "Z", MdbBus::BILL_ACCEPT_TIMEOUT);
                if (nrv < 0) grv = serv->report_fail("cash_accept.bill.double_accept", nrv);
                continue;
          }
	  if (serv->get_bill_escrow() == 0) break;
	  usleep(200*1000);
	};
	if (serv->get_bill_escrow()) {
	  sio_write(SIO_ERROR,
                    "could not return bill type %d from escrow, assume GONE",
                    serv->get_bill_escrow());
	  serv->reset_bill_escrow();
	};

	if (bb_ready == 2) {
	  rv = send_command("E2", "Z"); // re-enable bill acceptance	
	  if (rv < 0) grv = serv->report_fail("cash_accept.bill.reenable", rv);
	};	
  };

  if (accept) {
	//   ACCEPT coins - just verify variables actually
	if ((grv == 0) && (serv->get_escrow_total())) {
	  // accept coins now
	  int cval = 0;
	  for (int i=0; i<16; i++) 
		if (serv->get_coin_escrow(i)) {
		  cval += serv->get_coin_escrow(i) * cc_values[i];
                  serv->reset_coin_escrow(i);
		};
	  int prev_total = serv->get_escrow_total();
	  if (cval != serv->get_escrow_total()) {
		sio_write(SIO_ERROR, "numbers do not match: had %d in esc_coins, but %d in esc_total. all reset now.",
				  cval, serv->get_escrow_total());
	  };
	  serv->escrow_change("stack", 299, -serv->get_escrow_total());
	  sio_write(SIO_DATA, "CASH-DEPOSIT\t%d\t%d", 
                    min(prev_total, cval), 299);
	};
  } else {
	//	REJECT coins - return money (incl. money for unreturned bill)
	if ((grv==0) && serv->get_escrow_total()) { // if total is still not zero, it must be coins...
	  // lets start by going over coins routed to tubes
	  for (int i=0; i<16; i++)
		if (serv->get_coin_escrow(i) && 
			((cc_values[i]*serv->get_coin_escrow(i)) >= serv->get_escrow_total() )) { // never give out more then total in escrow
		  int cnt = serv->get_coin_escrow(i);
		  int rv = giveout_coins(i, cnt);
		  if (rv != cnt)
                      grv = serv->report_fail("cash_accept.coin.giveout", rv, 
                                          (boost::format("type=%d cnt=%d rv=%d")
                                            % i % cnt % rv).str());

		  if (serv->get_coin_escrow(i) != 0) {
			sio_write(SIO_ERROR, "could not return coin type %d from escrow: %d/%d given", i, rv, cnt);
		  };
		};
	};
	if (serv->get_escrow_total()) { // esc_total still not zero?
	  int amt = serv->get_escrow_total();
	  int rv = giveout_smart(amt);
	  if (rv != amt) 
              grv = serv->report_fail("cash_accept.giveout-smart", rv,
                                      (boost::format("total=%d req=%d")
                                       % serv->get_escrow_total() % amt).str());

	  if (serv->get_escrow_total() != 0) {
		sio_write(SIO_ERROR, "could not return money row: %d/%d given", rv, serv->get_escrow_total());
	  };
	};
  };

  return grv;
};

