#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <queue>

#include "servio.h"
#include "vmcserv.h"


// if set, enters 'free soda' mode
//   bit0 (1) - session started after init() message
//   bit1 (2) - any vend requests are automatically granted
// could be also changed using VMCCSD_FREE_VEND variable
int free_vend = 0;

int cur_state;  // current state
int cur_report; // if !0, will report current state at this time
int last_state; // last state sent to user

// expiration timer. should be reset to 0 any time session expires or device resets
extern time_t this_sess_expire;

#define VS_DISCONNECTED 		0
#define VS_DISABLED				1
#define VS_IDLE					2
#define VS_SESSION				3

char *state_names[] = {
  "DISCONNECTED", "DISABLED", "IDLE", "SESSION"
};

//
//
//            QUEUE MANGEMENT
//
//
class evt_response {
public:
  int event;
  int param;
};

std::queue<evt_response*> poll_evts;

void evt_enqueue(int event_, int param_) {
  if (event_ == EVTCMD_STATUS) {
	cur_report = 1;
	last_state = -1;
	return;
  };

  evt_response * evr = new evt_response();
  evr->event = event_;
  evr->param = param_;
  poll_evts.push(evr);
};


//
//
//          MAIN
//
//

void csd_init(){
  // return event 0 - reset = to reset the controller
  evt_enqueue(EVTCMD_RESET);
  char * c= getenv("VMCCSD_FREE_VEND");
  if (c) free_vend = atoi(c);
  if (free_vend)
	sio_write(SIO_WARN, "free-vend mode %d", free_vend);
  cur_state = VS_DISCONNECTED;
  cur_report = 1; // immediate report
  last_state = -1;
};

int csd_onidle() {
    if (cur_report > 0) {
	  if (cur_report <= time(0)) {
		if (last_state != cur_state) {
		  //sio_write(SIO_DATA, "VEND-STATE\t%s", (int)state_names[cur_state]);
		  sio_setvar("state", ":s", state_names[cur_state]);
		  last_state = cur_state;
		};
		cur_report = 0;
	  };
	};
};

int csd_command(char * cmd, int cmdlen, char * resp, int &resplen) {
  switch (cmd[0]) {
  case 0x10: // RESET
	evt_enqueue(EVTCMD_RESET);
	stat[STAT_MSGME]++;
    sio_write(SIO_DEBUG, "VMC reset");
	cur_state = VS_DISABLED;
	cur_report = time(0) + 10; // 10 second for reset startup
	this_sess_expire = 0;
    return CMD_OK;
  case 0x11: // SETUP
    if (cmdlen < 2) return CMD_MORE;
	stat[STAT_MSGME]++;
    switch (cmd[1]) {
    case 0x00: // get CONFIG data
      if (cmdlen < 6) return CMD_MORE;
      sio_write(SIO_DEBUG, "CSD setup/config (c2=%d, c3=%d)", cmd[2], cmd[3]);
      if (cmd[3]||cmd[4]||cmd[5]) {
		sio_write(SIO_DEBUG, "CSD host display present (%d,%d,%d)", cmd[3], cmd[4], cmd[5]);
      };
      resplen = 0;
	  evt_enqueue(1);
      return CMD_OK;
    case 0x01: // set MAX/MIN prices
      if (cmdlen < 6) return CMD_MORE;
      sio_write(SIO_DEBUG, "Machine Internal Prices: min=%d, max=%d", 
				*((unsigned short*)(cmd+3)), *((unsigned short*)(cmd+1)));
      return CMD_OK;
    };
    return CMD_FAIL;
  case 0x12:  // POLL
    if (!poll_evts.empty()) {
	  evt_response * evr = poll_evts.front();
	  poll_evts.pop();
 
      resplen = 1;
      resp[0] =  evr->event;
	  int arg = evr->param;
      switch (evr->event) {
      case 1: // reader config
		resplen = 8;
		resp[1] = 2; // level 1
		resp[2] = 0; resp[3] = 1; // USA country
		resp[4] = 1; // scale factor
		resp[5] = 2; // decimal places
		resp[6] = 10; // response time, sec
		resp[7] = 0x7; // multivend,display,refunds
		break;
      case 3: // begin session
		resplen = 10;
		if (arg <= 0) {
		  resp[2] = 0xFF; // unknown balance
		  resp[3] = 0xFF; 
		} else {
		  resp[2] = arg >> 8;
		  resp[3] = arg & 0xFF;
		};
		memset(resp+4, 0xFF, 4); // media ID unknown
		resp[7] = 0x01; // normal card
		resp[8]=resp[9]=0; //unused

		cur_state = VS_SESSION;
		cur_report = time(0) + 2; 
		break;
      case 5: // vend approved
		resplen = 3;
		resp[1] = 0xFF; resp[2] = 0xFF;
		break;
      };
	  stat[STAT_POLLRV] ++;
      
	  delete evr;
    } else {
	  stat[STAT_POLLME]++;
    };
    return CMD_OK;
  case 0x13: // VEND
	stat[STAT_MSGME]++;
    if (cmdlen < 2) return CMD_MORE;
    switch (cmd[1]) {
    case 0x00: // request
      if (cmdlen < 5) return CMD_MORE;
      sio_write(SIO_DATA, "VEND-REQUEST\t%d\t%d", 
		   (cmd[4]*0x100) | (cmd[5]&0xFF),
		   (cmd[2]*0x100) | (cmd[3]&0xFF)
		   );
      if (free_vend & 2) {
		// grant the request
		sio_write(SIO_DATA, "VEND-APPROVED");
		evt_enqueue(EVTCMD_APPROVED);
		return CMD_OK;
      };
	  return CMD_OK;
      break;
    case 0x01: // cancel
	  sio_write(SIO_DEBUG, "vend-cancel called");
	  evt_enqueue(EVTCMD_DENIED);
      return CMD_OK;
    case 0x02: // success
	  sio_write(SIO_DATA, "VEND-SUCCESS\t%d",
		   (cmd[2]*0x100) | (cmd[3]&0xFF)
		   );
      return CMD_OK;
    case 0x03: // failure
	  sio_write(SIO_DATA, "VEND-FAILED");
      return CMD_OK;
    case 0x04: // session complete
	  sio_write(SIO_DEBUG, "VMC session complete");
	  cur_state = VS_IDLE;
	  cur_report = time(0) + 10; 
	  this_sess_expire = 0;
	  evt_enqueue(EVTCMD_ENDSESS);
      return CMD_OK;
    case 0x05: // request
      if (cmdlen < 5) return CMD_MORE;
      sio_write(SIO_WARN, "CSD CASH SALE, price %d, item %d", 
		   (cmd[2]*0x100) | (cmd[3]&0xFF),
		   (cmd[4]*0x100) | (cmd[5]&0xFF)
		   );
    };
    break;
  case 0x14: // READER COMTROL
	stat[STAT_MSGME]++;
    if (cmdlen < 2) return CMD_MORE;
    switch (cmd[1]) {
    case 0x00: // disable
	  sio_write(SIO_DEBUG, "VEND-DISABLED");
	  sio_write(SIO_DEBUG, "VMC disabled us");
	  cur_state = VS_DISABLED;
	  cur_report = time(0) + 10; 
      return CMD_OK;
    case 0x01: // enable
	  //sio_write(SIO_DATA, "VEND-STATE\tIDLE");
	  sio_write(SIO_DATA, "VEND-READY");
	  cur_state = VS_IDLE;
	  cur_report = time(0) + 2; 

	  if (free_vend & 1) {
		sio_write(SIO_DATA, "VEND-SSTART\t-1");
		evt_enqueue(EVTCMD_BEGINSESS);
	  };
      return CMD_OK;
    case 0x02: // cancel
	  sio_write(SIO_DEBUG, "VEND-CANCEL");
	  evt_enqueue(8);
	  return CMD_OK;
    };
    break;
  case 0x17: // EXTENSION
    if (cmdlen < 2) return CMD_MORE;
    switch (cmd[1]) {
    case 0x00: // information
      if (cmdlen < 31) return CMD_MORE;
      sio_write(SIO_DEBUG, "CSD ext info (%d)", cmd[29]*0x100 | (cmd[30]&0xFF));
      resplen = 30;
      resp[0] = 0x9;
      memcpy(resp+1, "ZZZ", 3); // manufacturere ID
      memcpy(resp+4, "123456789012", 12); // serial Num
      memcpy(resp+16,"THEAMK MDSIM", 12); // model num
      resp[28]=0x03; resp[29]=0x00; // version
      return CMD_OK;
    };
    break;
  case 0x30: case 0x08: // reset other
	if (cmdlen < 1) return CMD_MORE;
	stat[STAT_RESETOTH]++;
	resplen = -1; //no ACK
	return CMD_OK;
  };
  return CMD_NOTSUPPORT;
};

