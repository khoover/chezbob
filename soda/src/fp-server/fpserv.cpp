#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <pthread.h>

#include <iostream>

#include <servio.h>

#include "fp_thread.h"

// $ g++ -I../lib fpserv.cpp -c -o fpserv.o
// $ g++ fpserv.o ../lib/servio.o -lfprint -o fpserv

void handle_start_learn(std::string id) {

}

int main(int argc, char** argv) {
  if (sio_open(argc, argv, "FPSERV", "1.34", "") < 0)
    exit(10);
  sio_write(SIO_DATA, "SYS-ACCEPT\tFP-");

  // Figure out what he's ignoring
  // Apparently nothing? perhaps kill this section
  std::string str;
  while (sio_read(str, 300) > 0) {
    std::cout << "here's a string: " << str << std::endl;
  };

  pthread_t reader_thread;
  int reader_thread_ret;
  char* reader_thread_name = "Fingerprint Reader Thread";

  reader_thread_ret = pthread_create(&reader_thread, NULL, fpthread, (void*) reader_thread_name);

  pthread_join(reader_thread, NULL);

  int ret_val;
  //while (true) {
  //  str = "";
  //  ret_val = sio_read(str, 1000);

  //  if(ret_val > 0) {
  //    std::string arg1 = sio_field(str, 0);
  //    std::string arg2 = sio_field(str, 1);

  //    std::cout << "Message received: " << str;
  //    std::cout << " arg1: " << arg1 << " arg2: " << arg2 << std::endl;
  //  }
  //}
  sio_close(-1, "NewFP server going down");

  return 0;
}

