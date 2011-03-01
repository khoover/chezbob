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
}

/*
  change amount of money in escrow and send out notifications
  args:
     trans  - string transaction type
     ptype  - misc info (bill /coin type)
     amount - amount to add (positive or negative)
 */
void MdbServ::escrow_change(const char * trans, int ptype, int amount) {
  esc_total += amount;
  sio_write(SIO_DATA, "CASH-ESCROW\t%d\t%s\t%d\t%d", esc_total, trans, ptype, amount);
  sio_setvar("escrow_last_amt", ":d",  amount);
  sio_setvar("escrow_last_type", ":d", ptype);
  sio_setvar("escrow_last_trans", ":s", trans);
  sio_setvar("escrow_total", "+:d", esc_total);
};

;
