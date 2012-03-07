#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <iostream>

#include <servio.h>

#include "fpserv_async.h"

// $ g++ -I../lib fpserv.cpp -c -o fpserv.o
// $ g++ fpserv.o ../lib/servio.o -lfprint -o fpserv

int state;
enum{ STATE_READ, STATE_LEARN, STATE_STOPPED };

int main(int argc, char** argv) {
  if (sio_open(argc, argv, "FPSERV", "2.0", "") < 0)
    exit(10);
  sio_write(SIO_DATA, "SYS-ACCEPT\tFP-");

  state = STATE_READ;
  std::string str;

  FPReader fp;
  fp.ChangeState(IDENTIFYING);

  struct timeval handle_fp_timeout;
  handle_fp_timeout.tv_sec = 0;
  handle_fp_timeout.tv_usec = 100*1000;

  int ret_val;
  while (true) {
    // Poll the fingerprint reader
    fp_handle_events_timeout(&handle_fp_timeout);
    fp.UpdateState();

    // Poll the bus and handle results
    str = "";
    ret_val = sio_read(str, 0);

    if(ret_val > 0) {
      std::string command = sio_field(str, 0);
      std::string userid = sio_field(str, 1);

      if(command == "FP-LEARN-START"){
        state = STATE_LEARN;
        fp.SetUsername(userid);
        fp.ChangeState(ENROLLING);
        // TODO: send messages back up when enrolling finishes
        //       sio_write(SIO_DATA, "FP-LEARN-GOOD");
        //sio_write(SIO_DATA, "FP-LEARN-FAIL");
      }
      else if(command == "FP-LEARN-STOP"){
        state = STATE_READ;
        fp.SetUsername("not-a-user:identifying-mode");
        fp.ChangeState(IDENTIFYING);
      }
      else{
        std::cout << "Message received: " << str;
        std::cout << " arg1: " << command << " arg2: " << userid << std::endl;
      }
    }
  }
  sio_close(-1, "NewFP server going down");

  return 0;
}

