extern "C" {
#include <signal.h>
}

#include "mdbserv.h"

//
//  P-115 interface required
//  DIP switch settings:
//      1 -  ON (cc present)
//      2 -  ON (bb present)
//      3 -  ON (200ms polling)
//      4 -  OFF (IMPORTANT!! no event mode)

int stop_num = 0;

void onsignal(int num) { 
  stop_num = num;
};

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
        /* stop_num is how we collect signals */
        stop_num = max(stop_num, mdbserv.sio_poll(sleep_for));
        if (stop_num != 0) break;
        stop_num = max(stop_num, mdbserv.mdb_poll(sleep_for));
  };
  
  sio_close(stop_num, "Signal Recieved");
};
