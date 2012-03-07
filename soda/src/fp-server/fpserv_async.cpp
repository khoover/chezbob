#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <unistd.h>

#include "fpserv_async.h"

// Notes: you cannot call a Start function from a callback. I don't know why;
// libfprint throws an error

FPReader::FPReader(fp_dev* device_) {
  device = device_;
  state = NONE;
  next = NONE;

  user_array = (fp_print_data**) malloc(sizeof(fp_print_data*));
  user_array[0] = NULL;
}

// This marks a new state that we hope to be in.
// Eventually, FPReader will swing itself around to be in this state.
// Try calling UpdateState a few times...?
void FPReader::ChangeState(SingleState newstate) {
  next = newstate;
}

// Effects a state change.
// If called with NONE, will look at the next instance variable
void FPReader::UpdateState() {
  // NOT FULLY IMPLEMENTED

  if(state == NONE && next == IDENTIFYING) {
    StartIdentify();
  }
  if(state == NONE && next == ENROLLING) {
    StartEnroll();
  }

  if(state == IDENTIFYING && next == IDENTIFYING) {
    next = NONE;
  }
  if(state == ENROLLING && next == ENROLLING) {
    next = NONE;
  }

  if(state == ENROLLING && next == IDENTIFYING) {
    // We need this handler to finish before we can call StartIdentify.
    // The next call to ChangeState will handle this case.
    state = NONE;
    StopEnroll();
  }
  if(state == IDENTIFYING && next == ENROLLING) {
    state = NONE;
    StopIdentify();
  }
}

void FPReader::AddUser(User* u) {
  if(user_array) {
    free(user_array);
  }

  users.push_back(u);

  user_array = (fp_print_data**) malloc(sizeof(fp_print_data*) * (users.size()+1));
  int i = 0;
  for(std::vector<User*>::iterator iter = users.begin();
      iter < users.end();
      iter++, i++) {
    user_array[i] = (*iter)->print;
  }
  user_array[users.size()] = NULL;
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
      AddUser(new User(print, "a user"));
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

  if(img) {
    fp_img_save_to_file(img, "file.pgm");
    fp_img_free(img);
  }
  if(print && result != FP_ENROLL_COMPLETE) {
    fp_print_data_free(print);
  }
}

void FPReader::EnrollStopCallback() {
  state = NONE;
  //TODO: check for next stage. make call.
  printf("Enroll stopped.\n");

  ChangeState(IDENTIFYING);

  //StartIdentify();
}

void FPReader::IdentifyCallback(int result, size_t match_offset, struct fp_img *img) {
  // If we don't immediately stop, the driver gets all excited.
  // In our StopIdentify handler, we'll start identifying again
  StopIdentify();

  switch(result) {
    case FP_VERIFY_NO_MATCH:
      // Did not find
      printf("No match found\n");
      break;
    case FP_VERIFY_MATCH:
      // Found it
      printf("Match found at %Zu\n", match_offset);
      break;
    case FP_VERIFY_RETRY:
      // poor scan quality
      printf("Match failed due to scan quality\n");
      break;
    case FP_VERIFY_RETRY_TOO_SHORT:
      // swipe too short. Not an issue with this reader.
      printf("Match failed, swipe longer\n");
      break;
    case FP_VERIFY_RETRY_CENTER_FINGER:
      // center finger.
      printf("Match failed, center finger and try again\n");
    case FP_VERIFY_RETRY_REMOVE_FINGER:
      // pressed too hard
      printf("Match failed, remove finger and try again\n");
      break;
    default:
      printf("Identify returned, no idea what's going on");
      break;
  }

  if(img) {
    fp_img_free(img);
  }
}

void FPReader::IdentifyStopCallback() {
  state = NONE;
  printf("Identify stopped\n");
}






int FPReader::StartEnroll() {
  state = ENROLLING;
  return fp_async_enroll_start(device, &enroll_stage_cb, this);
}

int FPReader::StopEnroll() {
  return fp_async_enroll_stop(device, &enroll_stop_cb, this);
}
int FPReader::StartIdentify() {
  state = IDENTIFYING;
  return fp_async_identify_start(device, user_array, &identify_cb, this);
}
int FPReader::StopIdentify() {
  return fp_async_identify_stop(device, &identify_stop_cb, this);
}

User::User(fp_print_data* fingerprint_, std::string username_) {
  print = fingerprint_;
  username = username_;
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

  while(true) {
    fp_handle_events();
    fp.UpdateState();
  }

  fp_dev_close(device);
  fp_exit();

  printf("complete\n");
}

