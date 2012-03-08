#include "fpserv_async.h"

int main(int argc, char** argv) {
  FPReader fp;

  fp.StartEnroll();

  fp_handle_events();

  fp.StopEnroll();
  fp_handle_events();
  fp_handle_events();
  fp_handle_events();
}
