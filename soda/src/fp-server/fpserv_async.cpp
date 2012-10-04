#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
#include <signal.h>

#include "fpserv_async.h"

// Notes: you cannot call a Start function from a callback. I don't know why;
// libfprint throws an error.
bool FPReader::fp_initialized = false;

void FPReader::InitializeFP() {
  if(fp_init() != 0) {
    printf("ERROR: libfprint failed to initialize\n");
    exit(0);
  }
  //fp_set_debug(1000);

  fp_initialized = true;
}

FPReader::FPReader() {
  if(!fp_initialized) {
    FPReader::InitializeFP();
    fp_initialized = true;
  }

  device = NULL;
  state = NONE;
  next = NONE;

  db = new DB();
  if(db) {
    users = db->GetUsers();
    printf("Loaded %d fingerprints.\n", users.size());
  } else {
    printf("Fingerprint DB failed to load.");
  }

  user_array = NULL;
  SetUsersArray();

  OpenDevice();
}

FPReader::~FPReader() {
  if(device) {
    fp_dev_close(device);
  }
  fp_exit();
}

// This marks a new state that we hope to be in.
// Eventually, FPReader will swing itself around to be in this state.
// Try calling UpdateState a few times.
void FPReader::ChangeState(SingleState newstate) {
  printf("Changing state from %s to %s.\n", STATESTRING(state), STATESTRING(newstate));
  next = newstate;
}

// Effects a state change.
// If called with NONE, will look at the next instance variable
void FPReader::UpdateState() {
  if(state == NONE && next == IDENTIFYING) {
    StartIdentify();
    state = IDENTIFYING;
    next = NONE;
  }
  if(state == NONE && next == ENROLLING) {
    StartEnroll();
    state = ENROLLING;
    next = NONE;
  }

  if(state == WAITING && next == IDENTIFYING) {
    // Do nothing
  }
  if(state == WAITING && next == ENROLLING) {
    // Do nothing
  }

  //if(state == IDENTIFYING && next == IDENTIFYING) {
  //  next = NONE;
  //}
  //if(state == ENROLLING && next == ENROLLING) {
  //  next = NONE;
  //}

  if(state == ENROLLING && next == IDENTIFYING) {
    // We need this handler to finish before we can call StartIdentify.
    // The next call to ChangeState will handle this case.
    StopEnroll();
  }
  if(state == IDENTIFYING && next == ENROLLING) {
    StopIdentify();
  }
}

void FPReader::SetUsername(std::string username) {
  enrollingUser = username;
}

void FPReader::AddUser(User* u) {
  if(user_array) {
    free(user_array);
  }
  if(db) {
    if(db->SaveUser(u)) {
      printf("User saved\n");
    } else {
      printf("User saving failed\n");
    }
  }

  users.push_back(u);
  SetUsersArray();
}

void FPReader::SetUsersArray() {
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

  User* u;

  switch (result) {
    case FP_ENROLL_COMPLETE:
      u = new User(print, enrollingUser);
      AddUser(u);
      SendLearnGood(u);
      StopEnroll();
      break;
    case FP_ENROLL_PASS:
      SendLearnBad("Please try again.");
      break;
    case FP_ENROLL_FAIL:
      SendLearnBad("Failed. Please try again.");
      break;
    case FP_ENROLL_RETRY:
      SendLearnBad("Bad scan. Please try again.");
      break;
    case FP_ENROLL_RETRY_TOO_SHORT:
      SendLearnBad("Swipe too short. Please try again.");
      break;
    case FP_ENROLL_RETRY_CENTER_FINGER:
      SendLearnBad("Finger not centered. Please try again.");
      break;
    case FP_ENROLL_RETRY_REMOVE_FINGER:
      SendLearnBad("Remove your finger and try again.");
      break;
    default:
      SendLearnBad("Unknown error in enrollment!");
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
  //TODO: assert state == WAITING
  state = NONE;
  printf("Enroll stopped.\n");

  ChangeState(IDENTIFYING);
}

void FPReader::IdentifyCallback(int result, size_t match_offset, struct fp_img *img) {
  printf("Identify callbacked\n");
  // If we don't immediately stop, the driver gets all excited.
  // In our StopIdentify handler, we'll start identifying again
  StopIdentify();

  // Mark down that we want to continue identifying
  next = IDENTIFYING;

  switch(result) {
    case FP_VERIFY_NO_MATCH:
      // Did not find
      SendBadRead("Fingerprint not recognized.");
      break;
    case FP_VERIFY_MATCH:
      // Found it
      SendGoodRead(users[match_offset]);
      break;
    case FP_VERIFY_RETRY:
      // poor scan quality
      SendBadRead("Fingerprint failed due to poor scan quality.");
      break;
    case FP_VERIFY_RETRY_TOO_SHORT:
      // swipe too short. Not an issue with this reader.
      SendBadRead("Fingerprint failed. Try again.");
      break;
    case FP_VERIFY_RETRY_CENTER_FINGER:
      // center finger.
      SendBadRead("Fingerprint failed. Center your finger and try again.");
      break;
    case FP_VERIFY_RETRY_REMOVE_FINGER:
      // pressed too hard
      SendBadRead("Fingerprint failed. Lift your finger and try again.");
      break;
    default:
      SendBadRead("Fingerprint failed for an uknown reason.");
      break;
  }

  if(img) {
    fp_img_free(img);
  }
}

void FPReader::IdentifyStopCallback() {
  //TODO: assert state == WAITING
  state = NONE;
  printf("Identify stopped\n");
}


int FPReader::StartEnroll() {
  printf("StartEnroll()\n");
  state = ENROLLING;
  return fp_async_enroll_start(device, &enroll_stage_cb, this);
}

int FPReader::StopEnroll() {
  state = WAITING;
  printf("StopEnroll()\n");
  return fp_async_enroll_stop(device, &enroll_stop_cb, this);
}
int FPReader::StartIdentify() {
  printf("StartIdentify()\n");
  state = IDENTIFYING;
  return fp_async_identify_start(device, user_array, &identify_cb, this);
}
int FPReader::StopIdentify() {
  state = WAITING;
  printf("StopIdentify()\n");
  return fp_async_identify_stop(device, &identify_stop_cb, this);
}

User::User(fp_print_data* fingerprint_, std::string username_) {
  print = fingerprint_;
  username = username_;
}

// By using this, you ignore the case where there might be multiple devices.
// You _must_ have called fp_init before calling this function.
bool FPReader::OpenDevice() {
  fp_dscv_dev** handle = NULL;
  fp_dscv_dev** p = NULL;
  fp_dev* to_ret = NULL;

  handle = fp_discover_devs();
  if(!handle) {
    return NULL;
  }

  p = handle;
  while(*p) {
    device = fp_dev_open(*p);

    printf("after open: 0x%x\n", device);
    if(device) {
      break;
    }

    p++;
  }

  // TODO: if device is null, throw an exception
  if(!device) {
    printf("DEVICE NOT OPEN. CRASH IMMINENT\n");
  }

  fp_dscv_devs_free(handle);
}

void FPReader::SendGoodRead(User* u) {
  if(u) {
    printf("Sending good read for %s\n", u->username.c_str());
    sio_write(SIO_DATA, "FP-GOODREAD\t%s", u->username.c_str());
  } else {
    sio_write(SIO_DATA, "FP-GOODREAD\t%s", "bad-user:null-pointer");
  }
}
void FPReader::SendBadRead(std::string message) {
  printf("Sending bad read: %s\n", message.c_str());
  sio_write(SIO_DATA, "FP-BADREAD\t%s", message.c_str());
}
void FPReader::SendLearnGood(User* u) {
  printf("Sending learn-good]n");
  sio_write(SIO_DATA, "FP-LEARN-GOOD");
}
void FPReader::SendLearnBad(std::string message) {
  printf("Sending learn-fail: %s\n", message.c_str());
  sio_write(SIO_DATA, "FP-LEARN-FAIL\t%s", message.c_str());
}

//int main(int argc, char** argv) {
//  FPReader fp;
//  std::string s = "kmowery";
//
//  fp.SetUsername(s);
//  fp.StartEnroll();
//
//  while(true) {
//    fp_handle_events();
//    fp.UpdateState();
//  }
//
//  printf("complete\n");
//}

void dev_open_cb(struct fp_dev* dev,
                 int status,
                 void *user_data) {
  if(user_data) {
    ((FPReader*) user_data)->OpenCallback(status);
  }
}

void enroll_stage_cb(struct fp_dev *dev,
                     int result,
                     struct fp_print_data *print,
                     struct fp_img *img,
                     void *user_data) {
  if(user_data) {
    ((FPReader*) user_data)->EnrollStageCallback(result, print, img);
  }
}
void enroll_stop_cb(struct fp_dev *dev,
                    void *user_data) {
  if(user_data) {
    ((FPReader*) user_data)->EnrollStopCallback();
  }
}
void identify_cb(struct fp_dev *dev,
                 int result,
                 size_t match_offset,
                 struct fp_img *img,
                 void *user_data) {
  if(user_data) {
    ((FPReader*) user_data)->IdentifyCallback(result, match_offset, img);
  }
}
void identify_stop_cb(struct fp_dev *dev,
                      void *user_data) {
  if(user_data) {
    ((FPReader*) user_data)->IdentifyStopCallback();
  }
}
