#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <unistd.h>

#include <libfprint/fprint.h>

void dev_open_cb(struct fp_dev* dev, int status, void *user_data);
void enroll_stage_cb(struct fp_dev *dev, int result,
                     struct fp_print_data *print, struct fp_img *img, void *user_data);
void enroll_stop_cb(struct fp_dev *dev, void *user_data);


void dev_open_cb(struct fp_dev* dev, int status, void *user_data) {
  printf("device opened with status %d\n", status);
  printf("device obj: 0x%x\n", dev);
  printf("starting enroll...\n");

  fp_async_enroll_start(dev, &enroll_stage_cb, NULL);
  printf("done.\n");
}

void enroll_stage_cb(struct fp_dev *dev, int result,
                     struct fp_print_data *print, struct fp_img *img, void *user_data) {
  if(result < 0) {
    printf("result negative: %d\n", result);
  }

  switch (result) {
    case FP_ENROLL_COMPLETE:
      printf("<b>Enrollment completed!</b>\n");
      fp_async_enroll_stop(dev, &enroll_stop_cb, NULL);
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

void enroll_stop_cb(struct fp_dev *dev, void *user_data) {
  printf("enroll stopped\n");
}

//int run_enroll(fp_dev* device, fp_print_data** print_data) {
//  if(!device) {
//    return -1;
//  }
//
//  int code= FP_ENROLL_PASS;
//  int stages = fp_dev_get_nr_enroll_stages(device);
//
//  fp_print_data* data = NULL;
//  fp_img* img = NULL;
//
//  // The Microsoft fingerprint reader has a single stage. Loop shouldn't matter.
//  //for(int i = 0; i < stages; i++) {
//  while(code == FP_ENROLL_PASS ||
//        code == FP_ENROLL_RETRY ||
//        code == FP_ENROLL_RETRY_TOO_SHORT ||
//        code == FP_ENROLL_RETRY_CENTER_FINGER ||
//        code == FP_ENROLL_RETRY_REMOVE_FINGER
//        ) {
//    code = fp_enroll_finger_img(device, &data, &img);
//    printf("code is %d\n", code);
//    fp_img_save_to_file(img, "file.pgm");
//
//    if(code == FP_ENROLL_FAIL) {
//      return code;
//    }
//
//    if(code == FP_ENROLL_COMPLETE) {
//      *print_data = data;
//      return code;
//    }
//
//    // TODO:do a thing with these
//    fp_print_data_free(data);
//    fp_img_free(img);
//  }
//
//  return code;
//}

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

  //if(!device) {
  //  printf("no devices found\n");
  //  exit(-1);
  //}

  printf("starting async enroll\n");

  sleep(4);

  //int code;
  //fp_print_data *data = NULL;
  //fp_img* img = NULL;
  //code = fp_enroll_finger_img(device, &data, &img);
  if(0 > fp_async_enroll_start(device, &enroll_stage_cb, NULL)) {
    printf("enrolling failed\n");
  }

  printf("done with main\n");

  fp_handle_events();
  fp_handle_events();
  fp_handle_events();
  fp_handle_events();
  fp_handle_events();
  fp_handle_events();
  fp_handle_events();

  sleep(5);

  printf("stopping\n");


  fp_async_enroll_stop(device, &enroll_stop_cb, NULL);
  while(true)
    fp_handle_events();

  //sleep(30);


  fp_dev_close(device);
  fp_exit();

  printf("complete\n");
}

