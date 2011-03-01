#ifndef _MDBSERV_H_
#define _MDBSERV_H_

#define VERSION   "3.00"

#include <algorithm>
#include <string>
#include <cerrno>

#include <boost/format.hpp>

extern "C" {
#include <glob.h>
}

using std::max;
using std::min;

#include "servio.h"
#include "sercom.h"

class MdbServ;

class MdbBus
{
public:
    MdbBus(MdbServ *mdbserv)
        :serv(mdbserv)
    {
        ser_port = strdup("/dev/ttyUSB0");
    }
    ~MdbBus()
    {
      if (srh)
            ser_close(srh);
    }

    void init()
    {
        char cmd[1024];

        cc_ready = 0;
        bb_ready = 0;
        next_scan = 0;
        want_enabled = 0;

        sio_getvar("enabled", "D+:d", &want_enabled);
        sio_getvar("port", "D:s", &ser_port);

        if (!open_serport()) {
            while (sio_read(cmd, sizeof(cmd), 100) > 0) {};
            sio_close(2, "serial port open failed");
            exit(2);
        };
    }

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

    int poll(int &sleep_for)
    {
        int stop_num = 0;

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

        return stop_num;
    }

    // init coinchanger
    //   returns -1 on error or timeout, or 0 if init  ok and all ready
    // also sets cc_ready
    int cc_init();

    // init bill acceptor
    //   returns -2 on timeout, -1 on error, or 0 if init  ok and all ready
    // also sets bb_ready
    int bb_init();

    // poll the coinchanger
    int cc_poll();

    int bb_stacker_refresh(int forceprint);

    int bb_poll();

    // give given number of coins of this type
    // RV is number of coins given sucessfully
    //  or -1/-2 if error occur before first coin was given
    // it also decreases escrow amount if it can, and sends -ESCROW messages as it does so
    int giveout_coins(int type, int count);

    // forceprint:
    //   0 print if changed
    //   1 print always
    //   -1 print as changed, do not scan tube full
    int cc_tube_refresh(int forceprint);

    void cash_reset();

    // accept/reject stuff in escrow
    int cash_accept(bool accept, int amt=0);

    // gives given amount using availible coins of higest denomination
    // RV is amount given sucessfully
    //  or -1/-2 if error occur before first coin was given
    // uses giveout_coins with all of its side effects
    int giveout_smart(int amount);

    int dispense_coints(int denom, int count, int *type)
    {
        *type = -1;
        for (int i=0; i<16; i++)
            if ((cc_values[i] == denom) && (cc_count[i]>=count)) {
                *type = i;
                break;
            };

        int rv = -1;
        if (*type > -1) rv = giveout_coins(*type, count);
        return rv;
    }

    int set_manual_disp(int denom, int mode)
    {
        for (int i=0; i<16; i++)
            if ((denom==0) || (cc_values[i] == denom)) {
                cc_mandisp[i] = mode;
            };
        cc_tube_refresh(0);
    }

    void refresh_all(bool forceprint)
    {
        cc_tube_refresh(forceprint);
        bb_stacker_refresh(forceprint);
    }

// send_command
//   send string in "cmd"
//   wait up to timeout ms for response
//   returns -2 on timeout, -1 on error (link or protocol), 1 if response recieved 
// when expect==NULL, the parsed answer is stored into "resp" buffer as following:
//   resp[0] - first response character unchanged
//   resp[1] - second nonspace response character unchager when resp[0] in P,Q,I
//   resp[...]  - hex-decoded rest of the strings (up to resp[resplen-1])
//   rest of resp is filld with 0's - always 
// when expect!=NULL, it must match coresponding resp characters, and those charactes would be 
// removed from resp.
// the "X" codes are always parsed and handled as an error
////int send_command(const char * cmd, char* expect=0, int timeout = 1000);
    int send_command(const char *cmd, const char *expect=NULL, int timeout = 1000);

    void flush_buffer();

    unsigned char resp[64];
    int resplen;
    /* raw string (ASCII only, no nonprintables */
    char resp_raw[255];

    SER_HANDLE srh;
    char * ser_port;
/*
// response code for send_command
MDBEXT unsigned char resp[64];
MDBEXT int  resplen;
MDBEXT char resp_raw[255];  // raw string (ASCII only, no nonprintables)
*/
// changegiver settings (filled at coin_init() )
    int cc_ready;       // 0 = not ready, 1 = ready/disabled, 2 = ready/enabled
    int cc_values[16];  // coin values, scaled to cents
    bool cc_full[16];   // tube full status
    int cc_count[16];   // coin count in each tube
    int cc_mandisp[16]; // min # of coins i the tube for dispensing to be enabled
    int cc_man_ok;      // set of tubes where manual dispensing was allowed (bitarray)



// bill validator settings (filled at bval_init() )
    int bb_ready;       // 0 = not ready, 1 = ready/disabled, 2 = ready/enabled
    int bb_values[16];  // bill values, scaled
    int bb_capacity;    // bill stacker capacity
    int bb_stacked;     // bills stacked
    bool bb_full;       // true = bill stacker full

    int next_scan;

    class MdbServ *serv;

// the enabling mask
// will auto-enable devices when they go online
//   bit 0 (1)   - enable coins
//   bit 1 (2)   - enable bill validaor
    int want_enabled;
};

class MdbServ
{
public:
    MdbServ(int argc, char**argv)
        :bus(this)
    {

        if (sio_open(argc, argv, "MDBSERV", VERSION, "") < 0) {
            exit(11);
        };

        sio_write(SIO_DATA, "SYS-ACCEPT\tCASH-\tSYS-SET");

        init();
        bus.init();
    }

    ~MdbServ()
    {
        bus.cash_reset(); // return stuff in escrow
    }

    void init()
    {
        esc_total = 0;
        esc_bill = 0;
        bzero(esc_coins, sizeof(esc_coins));
        escrow_change("reset", 0, 0);
    }

    int sio_poll(int &sleep_for)
    {
        char cmd[1024];
        char * cmdv[16];
        int cmdc;
        int cmdlen;

        int stop_num = 0;

	bus.flush_buffer();

	errno = 0;
	if ((cmdlen=sio_read(cmd,sizeof(cmd),sleep_for))>0) {
	  cmdc = sio_parse(cmd, cmdv, sizeof(cmdv));
	  if (strncmp(cmdv[0], "CASH-", 5) == 0) {
	    sio_write(SIO_DEBUG|15, "DO-COMMAND\t%s", cmd);
	  };

	  if (strcmp(cmdv[0], "CASH-RESET")==0) {
		bus.cash_reset();
	  } else if (strcmp(cmdv[0], "CASH-ACCEPT")==0) {
		int amt = 0;
		if ((cmdc>1)) amt = atoi(cmdv[1]);
		bus.cash_accept(1);
		if (esc_total) {
		  sio_write(SIO_DATA, "CASH-FAIL\t%d", esc_total);
		} else {
		  sio_write(SIO_DATA, "CASH-OK");
		};
	  } else if (strcmp(cmdv[0], "CASH-REJECT")==0) {
		bus.cash_accept(0);
		if (esc_total) {
		  sio_write(SIO_DATA, "CASH-FAIL\t%d", esc_total);
		} else {
		  sio_write(SIO_DATA, "CASH-OK");
		};
	  } else if (strcmp(cmdv[0], "CASH-STATUS")==0) {
              bus.refresh_all(true);
		sio_write(SIO_DATA, "CASH-ESCROW\t%d\t%d\t%d", esc_total, 0, 0);
	  } else if ((strcmp(cmdv[0], "CASH-CHANGE-MAN")==0) && (cmdc==3)) {
		int denom = atoi(cmdv[1]);
		int count = atoi(cmdv[2]);

                int type;
                int rv = bus.dispense_coints(denom, count, &type);


		if (rv != count) {
		  report_fail("cash-change-man.giveout", rv, 
                              (boost::format("type=%d cnt=%d rv=%d")
                                            % type % count % rv).str());

		  sio_write(SIO_DATA, "CASH-FAIL\t%d", std::max(rv,0)*denom);
		} else {
		  sio_write(SIO_DATA, "CASH-OK");
		};	
	  } else if ((strcmp(cmdv[0], "CASH-CHANGE")==0) && (cmdc==2)) {
		int amount = atoi(cmdv[1]);
		int rv = bus.giveout_smart(amount);
		if (rv != amount) {
		  report_fail("cash-change.giveout-smart", rv,
                              (boost::format("req=%d") %amount).str());
		  sio_write(SIO_DATA, "CASH-FAIL\t%d", max(0, rv));
		} else {
		  sio_write(SIO_DATA, "CASH-OK");
		};	
	  } else if ((strcmp(cmdv[0], "CASH-MANUAL-DISP")==0) && (cmdc==3)) {
		int denom = atoi(cmdv[1]);
		int mode = atoi(cmdv[2]);

                /* XXX The comment elsewhere suggests this is the min number
                 * of coins to be able to dispense
                 */
                bus.set_manual_disp(denom, mode);

		sio_write(SIO_DATA, "CASH-OK");
	  } else if (strncmp(cmdv[0], "CASH-", 5)==0) {
		sio_write(SIO_DEBUG, "unparseable CASH- command\t%s\t%s\t%s",
				  (cmdv[0]?cmdv[0]:"{null}"),
				  (cmdv[1]?cmdv[1]:"{null}"),
				  (cmdv[2]?cmdv[2]:"{null}"));
	  };
	};

	if (cmdlen == -1) {
	  // server died
	  stop_num = errno + 1000;
	};

        return stop_num;
    }

    int mdb_poll(int &sleep_for)
    {
        return bus.poll(sleep_for);
    }

    int report_fail(const char * where,
                    int code = 0,
                    const std::string msg = "");

    void update_coin_escrow(int slot, int delta)
    {
        esc_coins[slot] += delta;
    }

    void reset_coin_escrow(int slot) { esc_coins[slot] = 0; }

    int get_escrow_total() { return esc_total; }

    int get_coin_escrow(int slot) { return esc_coins[slot]; }
    int get_bill_escrow() { return esc_bill; }

    void update_bill_escrow(int delta)
    {
        esc_bill += delta;
    }

    void reset_bill_escrow() { esc_bill = 0; }

    // notify of escrow change. should be the only thing that changes the var except reset
    void escrow_change(const char * trans, int ptype, int amount);

    void set_escrow_variables()
    {
        sio_setvar("escrow_bill", "+:d", esc_bill);
        sio_setvar("escrow_total", "+:d", esc_total);
    }

    // virtual escrow settings
    int esc_total;      // total amount of money in the escrow
    int esc_coins[16];  // coint for each coin type
    int esc_bill;       // bb escrow: 0 if empty, 100+billnum otherwise

    MdbBus bus;
};


bool strbegins(const char * slong, const char * sshort);

int ascii_to_hex1(char c);
int ascii_to_hex2(char * cc);

#endif
