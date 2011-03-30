extern "C" {
#include <signal.h>
}

#include "sndserv.h"

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

  SndServ sndserv(argc, argv);
  
  
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
      stop_num = std::max(stop_num, sndserv.sio_poll(1000));
  };
  
  sio_close(stop_num, "Signal Recieved");
};
