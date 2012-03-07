#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <unistd.h>

#include "fpserv_async.h"


FPReader::FPReader(fp_dev* device_) {
  device = device_;
  state = NONE;
  next = NONE;
}

void FPReader::ChangeState(Action a) {

}

void FPReader::OpenCallback(int status) {
  // Probably won't use? Figure out.
}

void FPReader::EnrollStageCallback(int result, struct fp_print_data* print, struct fp_img* img) {
  printf("Enroll stage callbacked!");
  if(result < 0) {
    printf("result negative: %d\n", result);
  }

  switch (result) {
    case FP_ENROLL_COMPLETE:
      printf("<b>Enrollment completed!</b>\n");
      StopEnroll();
      break;
    case FP_ENROLL_PASS:
      printf("<b>Step %d of %d</b>\n", 0, 146789);
      break;
    case FP_ENROLL_FAIL:
      printf("<b>Enrollment failed!</b>\n");
      break;
    case FP_ENROLL_RETRY:
      printf("<b>Bad scan. Please try again.</b>\n");
      break;
    case FP_ENROLL_RETRY_TOO_SHORT:
      printf("<b>Bad scan: swipe was too short. Please try again.</b>\n");
      break;
    case FP_ENROLL_RETRY_CENTER_FINGER:
      printf("<b>Bad scan: finger was not centered on scanner. Please "
        "try again.</b>\n");
      break;
    case FP_ENROLL_RETRY_REMOVE_FINGER:
      printf("<b>Bad scan: please remove finger before retrying.</b>\n");
      break;
    default:
      printf("Unknown state!\n");
  }
}

void FPReader::EnrollStopCallback() {
  //TODO: check for next stage. make call.
  printf("Enroll stopped.");
}

void FPReader::IdentifyCallback(int result, size_t match_offset, struct fp_img *img) {}
void FPReader::IdentifyStopCallback() {}






int FPReader::StartEnroll() {
  state = ENROLLING;
  return fp_async_enroll_start(device, &enroll_stage_cb, this);
}

int FPReader::StopEnroll() {
  return fp_async_enroll_stop(device, &enroll_stop_cb, this);

}
int FPReader::StartIdentify() {
  state = IDENTIFYING;
  // TODO: put together a fingerprint gallery
  //return fp_async_identify_start(globalstate.device, &identify_cb, this);
}
int FPReader::StopIdentify() {
  return fp_async_identify_stop(device, &identify_stop_cb, this);
}

// Gets an opened fingerprint device, or NULL if none exist.
// By using this, you ignore the case where there might be multiple devices.
// You _must_ have called fp_init before calling this function.
fp_dev* get_device() {
  fp_dscv_dev** handle = NULL;
  fp_dscv_dev** p = NULL;
  fp_dev* to_ret = NULL;

  handle = fp_discover_devs();
  if(!handle) {
    return NULL;
  }

  p = handle;
  while(*p) {
    to_ret = fp_dev_open(*p);
    //fp_async_dev_open(*p, &dev_open_cb, NULL);

    printf("after open: 0x%x\n", to_ret);
    if(to_ret) {
      break;
    }

    p++;
  }

  fp_dscv_devs_free(handle);
  return to_ret;
}

int main(int argc, char** argv) {
  fp_init();
  fp_set_debug(1000);

  fp_dev* device = get_device();

  if(!device) {
    printf("no devices found\n");
    exit(-1);
  }

  FPReader fp(device);

  fp.StartEnroll();

  //printf("starting async enroll\n");

  //if(0 > fp_async_enroll_start(device, &enroll_stage_cb, NULL)) {
  //  printf("enrolling failed\n");
  //}

  //printf("done with main\n");

  //fp_handle_events();
  //fp_handle_events();
  //fp_handle_events();
  //fp_handle_events();
  //fp_handle_events();
  //fp_handle_events();
  //fp_handle_events();

  //sleep(5);

  //printf("stopping\n");

  //fp.StopEnroll();

  while(true)
    fp_handle_events();

  //sleep(30);


  fp_dev_close(device);
  fp_exit();

  printf("complete\n");
}

