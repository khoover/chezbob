#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <iostream>

#include <servio.h>

#include "fpserv_async.h"

int main(int argc, char** argv) {
  if (sio_open(argc, argv, "FPSERV", "2.0", "") < 0)
    exit(10);
  sio_write(SIO_DATA, "SYS-ACCEPT\tFP-");

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
        fp.SetUsername(userid);
        fp.ChangeState(ENROLLING);
      }
      else if(command == "FP-LEARN-STOP"){
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

