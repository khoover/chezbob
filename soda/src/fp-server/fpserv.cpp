#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <pthread.h>

#include <iostream>

#include <servio.h>

// $ g++ -I../lib fpserv.cpp -c -o fpserv.o
// $ g++ fpserv.o ../lib/servio.o -lfprint -o fpserv

int state;
enum{ STATE_READ, STATE_LEARN, STATE_STOPPED };

int main(int argc, char** argv) {
  if (sio_open(argc, argv, "FPSERV", "1.34", "") < 0)
    exit(10);
  sio_write(SIO_DATA, "SYS-ACCEPT\tFP-");

  state = STATE_READ;
  std::string str;

  int ret_val;
  while (true) {
    // Poll the fingerprint reader
    // TODO: poll it

    // Poll the bus and handle results
   str = "";
   ret_val = sio_read(str, 1000);

   if(ret_val > 0) {
     std::string command = sio_field(str, 0);
     std::string userid = sio_field(str, 1);

     if(command == "FP-LEARN-START"){

       state = STATE_LEARN;
       // TODO: Tell lib to do learning
       //       sio_write(SIO_DATA, "FP-LEARN-GOOD");
       sio_write(SIO_DATA, "FP-LEARN-FAIL");
     }
     else if(command == "FP-LEARN-STOP"){
       state = STATE_READ;
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

