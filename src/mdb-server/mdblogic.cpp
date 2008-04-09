#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <signal.h>


#include "sercom.h"
#include "servio.h"
#include "mdbserv.h"


//
//
//                     CASH CHANGER GENERAL
//
//
int cc_poll() {
  int ev_cnt = 0;
  while (send_command("P1") >= 0) {
	if (resp[0] == 'Z') {
	  return ev_cnt;

	} else if ((resp[0] == 'P') && (resp[1] == '1')) {
	  int i1 = resp[2];
	  sio_write(SIO_LOG, "accepted coin\t%d\t%d", i1, cc_values[i1]); 
	  if ((i1<0)||(i1>15)) i1 = 15;
	  esc_coins[i1]++;
	  cc_tube_refresh(0);
	  escrow_change("deposit", i1+200, cc_values[i1]);
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
	  sio_write(SIO_WARN, "unknown CC poll response: %s", (int)resp_raw);
	};
	ev_cnt++;
  };
  return -1;
};

int cc_tube_refresh(int forceprint) {
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
		report_fail("tube_refresh.set_manok");	  
	  send_command("E1", "Z"); // enable coin acceptance to action settings
	  if (cc_ready != 2) 
		if (send_command("D1", "Z") < 0) { // disable aceptance back if needed
		  sleep(1); send_command("D1", "Z");
		  report_fail("tube_refresh.set_manok.cleanup");	 
		};
	};

	if ((cc_ready == 1) && (want_enabled & 5)) {
	  // enable coin acceptance	
	  int rv = send_command("E1", "Z");
	  if (rv < 0) grv=report_fail("cash_enable.enable-coin-acceptance", rv);
	  else cc_ready = 2;
	};
	if ((cc_ready == 2) && !(want_enabled & 5)) {
	  // disable coin acceptance	
	  int rv = send_command("D1", "Z");
	  if (rv < 0) grv=report_fail("cash_enable.disable-coin-acceptance", rv);
	  else cc_ready = 1;
	};
  };

  // just in case...
  sio_setvar("escrow_total", "+:d", esc_total);
  sio_setvar("cc_ready", "+:d", cc_ready);

  return 0;
};


int cc_init() {
  char bf[512]; // 16 ctypes => 32 chars per cointype

  cc_ready = 0;
  // reset changegiver, disable acceptance
  if (send_command("R1", "Z", 2000) < 0) return -1;

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
  sio_write(SIO_DEBUG, "CC: coin values: %s", (int)bf);

  // get routing
  if (send_command("S3", "S3") < 0) return -1;
  bf[0] = 0;
  for (int i=0; i<16; i++) 
	if (((resp[1 - i/8] >> (i%8)) & 1) != 0) {
	  if (bf[0]) strcat(bf, ", ");
	  sprintf(strchr(bf, 0), "#%d", i);
	};
  sio_write(SIO_DEBUG, "CC: routed to tube: %s", (int)bf);

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
int giveout_coins(int type, int count) {
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
	rv = send_command(bf, "Z", 1000); 
	if (rv < 0) grv = report_fail("giveout_coins.giveout", rv);
	// poll every 100ms up to 10 sec, until results are ready
	for (int i=0; i<100; i++) {
	  rv = send_command("P1"); // poll until OK
	  if (rv<0) { grv = report_fail("giveout_coins.pollfail", rv); break; };
	  if (resp[0] == 'Z')  break; // got our response 
	  if (resp[0] != 'G') {
		grv = report_fail("giveout_coins.pollfail", 0, "invalid data: %s", (int)resp_raw); break;
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
	if (rv < 0) grv = report_fail("giveout_coins.reenable", rv);
  };
  
  // update escrow
  if (done) {
	int diff = cc_values[done]*done;
	if (diff> esc_total) diff = esc_total;
	escrow_change("return", type+200, -diff);

	esc_coins[type] -= done;
	if (esc_coins[type] < 0) esc_coins[type] = 0;
  };

  cc_tube_refresh(0);

  return done ? done : grv;
};

/*
  change amount of money in escrow and send out notifications
  args:
     trans  - string transaction type
     ptype  - misc info (bill /coin type)
     amount - amount to add (positive or negative)
 */
void escrow_change(char * trans, int ptype, int amount) {
  esc_total += amount;
  sio_write(SIO_DATA, "CASH-ESCROW\t%d\t%s\t%d\t%d", esc_total, trans, ptype, amount);
  sio_setvar("escrow_last_amt", ":d",  amount);
  sio_setvar("escrow_last_type", ":d", ptype);
  sio_setvar("escrow_last_trans", ":s", trans);
  sio_setvar("escrow_total", "+:d", esc_total);
};



int giveout_smart(int amount) {
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



//
//
//                     BILL ACCEPTOR GENERAL
//
//
int bb_poll() {
  int ev_cnt = 0;
  while (send_command("P2") >= 0) {
	int i1 = resp[2];

	if (resp[0] == 'Z') {
	  return ev_cnt;

	ev_cnt++;

	} else if ((resp[0] == 'Q') && (resp[1] == '1')) {
	  sio_write(SIO_LOG, "accepted bill\t%d\t%d", i1, bb_values[i1]); 
	  if ((i1<0)||(i1>15)) i1 = 15;

	  if (esc_bill != 0) {
	    sio_write(SIO_ERROR, "DOUBLE accept message - had %d, got %d, ignoring", esc_bill, 100+i1);
	  } else {
	    esc_bill = 100+i1;
	    bb_stacker_refresh(0);
	    escrow_change("deposit", esc_bill, bb_values[i1]);
	  };

	} else if ((resp[0] == 'Q') && (resp[1] == '2')) {
	  sio_write(SIO_LOG, "stacked bill\t%d\t%d", i1, bb_values[i1]); 
	  if ((i1+100) != esc_bill) {
		sio_write(SIO_ERROR, "MISMATCH between accept and stack: accept %d, stack %d", esc_bill, i1+100);
		// we will use whatever is stored
	  };
	  int val = 0;
	  if (esc_bill) {
		val = -bb_values[esc_bill-100];
		escrow_change("accept", esc_bill, val);
	  };
	  sio_write(SIO_DATA, "CASH-DEPOSIT\t%d\t%d", -val, 100+i1);
	  esc_bill = 0;
	  bb_stacker_refresh(0);

	} else if ((resp[0] == 'Q') && (resp[1] == '3')) {
	  sio_write(SIO_LOG, "returned bill\t%d\t%d", i1, bb_values[i1]); 
	  if ((i1+100) != esc_bill) {
		sio_write(SIO_ERROR, "MISMATCH between accept and return: accept %d, stack %d", esc_bill, i1+100);
	  };
	  if (esc_bill) {
		escrow_change("stack", esc_bill, -bb_values[esc_bill-100]);
	  };
	  esc_bill = 0;
	  bb_stacker_refresh(0);
	  
	} else if ((resp[0] == 'Q') && (resp[1] == '4')) {
	  sio_write(SIO_LOG, "rejected bill\t%d\t%d", i1, bb_values[i1]); 
	  if (esc_bill) {
	    sio_write(SIO_ERROR, "Got REJECT while having bill %d in escrow", esc_bill);
	  };
	  esc_bill = 0;
	  bb_stacker_refresh(0);

	} else {
	  sio_write(SIO_WARN, "unknown BB poll response: %s", (int)resp_raw);
	};
  };
  return -1;
};

int bb_stacker_refresh(int forceprint) {

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
	  if (rv < 0) grv=report_fail("cash_enable.enable-bill-acceptance", rv);
	  else bb_ready = 2;
	};
	// deactivate is needed
	if ((bb_ready==2) && (!(want_enabled & 3))) {
	  int rv = send_command("D2", "Z");
	  if (rv < 0) grv=report_fail("cash_enable.disable-bill-acceptance", rv);
	  else bb_ready = 1;
	};

  };

  // send variables
  sio_setvar("escrow_bill", "+:d", esc_bill);
  sio_setvar("bb_ready",    "+:d", bb_ready);
  sio_setvar("bb_full",     "+:d", bb_full);
  sio_setvar("bb_count",    "+:d", bb_stacked);


  return 0;

};

int bb_init() {

  char bf[512]; // 16 ctypes => 32 chars per cointype

  bb_ready = 0;
  // reset, disable acceptance
  if (send_command("R2", "Z", 2000) < 0) return -1;

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
  sio_write(SIO_DEBUG, "BB: bill values: %s", (int)bf);

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
void cash_reset() {
  int rv;
  // disable acceptance
  // TODO??

  if (rv < 0) report_fail("cash_reset.cash-disable", rv);
  // return stuff in escrow
  rv = cash_accept(0);
  if (rv < 0) report_fail("cash_reset.escrow-reject", rv);
  // request devices reset
  cc_ready = 0;
  bb_ready = 0;
};

// accept/reject stuff in escrow
int cash_accept(bool accept, int amt) {
  int grv = 0;

  if (accept && (amt != 0)) {
	return report_fail("non-zero amounts unsuported", amt);
  };

  //
  //    get rid of BILL
  //
  if (esc_bill) {
	const char * cmd = accept ? "K1": "K2";

	if ((!accept) && (bb_values[esc_bill-100] > esc_total)) {
	  // do not return bill if the money was returned by some other means (coins)
	  sio_write(SIO_ERROR, "not returning bill #%d (value %d), as escrow has %d", 
				esc_bill, bb_values[esc_bill-100], esc_total);
	  // accept it instead...
	  cmd = "K1";
	};

	send_command("D2", "Z"); // disable bill acceptance
	
	int rv = send_command(cmd, "Z", 3000);
	if (rv < 0) grv = report_fail("cash_accept.bill.reject", rv);
	for (int i=0; i<10*5; i++) { // wait up to 10 seconds for bill to be ejected
	  // poll bill acceptor until message handler clears esc_bill
	  rv = bb_poll();
	  if (rv < 0) grv = report_fail("cash_accept.bill.poll", rv);
	  if (esc_bill == 0) break;
	  usleep(200*1000);
	};
	if (esc_bill) {
	  sio_write(SIO_ERROR, "could not return bill type %d from escrow, assume GONE", esc_bill);
	  esc_bill = 0;
	};

	if (bb_ready == 2) {
	  rv = send_command("E2", "Z"); // re-enable bill acceptance	
	  if (rv < 0) grv = report_fail("cash_accept.bill.reenable", rv);
	};	
  };

  if (accept) {
	//   ACCEPT coins - just verify variables actually
	if ((grv == 0) && (esc_total)) {
	  // accept coins now
	  int cval = 0;
	  for (int i=0; i<16; i++) 
		if (esc_coins[i]) {
		  cval += esc_coins[i] * cc_values[i];
		  esc_coins[i] = 0;
		};
	  int prev_total = esc_total;
	  if (cval != esc_total) {
		sio_write(SIO_ERROR, "numbers do not match: had %d in esc_coins, but %d in esc_total. all reset now.",
				  cval, esc_total);
	  };
	  escrow_change("stack", 299, -esc_total);
	  sio_write(SIO_DATA, "CASH-DEPOSIT\t%d\t%d", min(prev_total, cval), 299);
	};
  } else {
	//	REJECT coins - return money (incl. money for unreturned bill)
	if ((grv==0) && esc_total) { // if total is still not zero, it must be coins...
	  // lets start by going over coins routed to tubes
	  for (int i=0; i<16; i++)
		if (esc_coins[i] && 
			((cc_values[i]*esc_coins[i]) >= esc_total )) { // never give out more then total in escrow
		  int cnt = esc_coins[i];
		  int rv = giveout_coins(i, cnt);
		  if (rv != cnt) grv = report_fail("cash_accept.coin.giveout", rv, "type=%d cnt=%d rv=%d", i, cnt, rv);
		  if (esc_coins[i] != 0) {
			sio_write(SIO_ERROR, "could not return coin type %d from escrow: %d/%d given", i, rv, cnt);
		  };
		};
	};
	if (esc_total) { // esc_total still not zero?
	  int amt = esc_total;
	  int rv = giveout_smart(amt);
	  if (rv != amt) grv = report_fail("cash_accept.giveout-smart", rv, "total=%d req=%d", esc_total, amt);
	  if (esc_total != 0) {
		sio_write(SIO_ERROR, "could not return money row: %d/%d given", rv, esc_total);
	  };
	};
  };

  return grv;
};

