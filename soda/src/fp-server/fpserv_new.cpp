#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include <libfprint/fprint.h>

#include "nbis/include/bozorth.h"

int run_enroll(fp_dev* device, fp_print_data** print_data) {
  if(!device) {
    return -1;
  }

  int code= FP_ENROLL_PASS;
  int stages = fp_dev_get_nr_enroll_stages(device);

  fp_print_data* data = NULL;
  fp_img* img = NULL;

  // The Microsoft fingerprint reader has a single stage. Loop shouldn't matter.
  //for(int i = 0; i < stages; i++) {
  while(code == FP_ENROLL_PASS ||
        code == FP_ENROLL_RETRY ||
        code == FP_ENROLL_RETRY_TOO_SHORT ||
        code == FP_ENROLL_RETRY_CENTER_FINGER ||
        code == FP_ENROLL_RETRY_REMOVE_FINGER
        ) {
    code = fp_enroll_finger_img(device, &data, &img);
    printf("code is %d\n", code);
    fp_img_save_to_file(img, "file.pgm");

    if(code == FP_ENROLL_FAIL) {
      return code;
    }

    if(code == FP_ENROLL_COMPLETE) {
      *print_data = data;
      return code;
    }

    // TODO:do a thing with these
    fp_print_data_free(data);
    fp_img_free(img);
  }

  return code;
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

  fp_dev* device = get_device();

  if(!device) {
    printf("no devices found\n");
    exit(-1);
  }

  int stages;
  stages = fp_dev_get_nr_enroll_stages(device);
  printf("%d stages\n", stages);

  if(fp_dev_supports_imaging(device)) {
    printf("Imaging supported!\n");
  }

  //fp_print_data *array = NULL;
  //size_t loc;
  //printf("identifying...\n");
  //int ret = fp_identify_finger(device, &array, &loc);
  //printf("return value: %d\n loc: %d\n", ret, loc);

  //fp_verify_finger_img(device, print_data, NULL);

  //printf("doing enroll\n");

  //fp_print_data* print_data = NULL;
  //run_enroll(device, &print_data);

  //int result;
  //printf("place finger again, please\n");
  //result = fp_verify_finger_img(device, print_data, NULL);
  //printf("code is %d\n", result);

  fp_dev_close(device);
  fp_exit();

  printf("complete\n");
}

