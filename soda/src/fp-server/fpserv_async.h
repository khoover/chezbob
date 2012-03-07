#ifndef FPSERV_ASYNC_H
#define FPSERV_ASYNC_H

#include <iostream>
#include <vector>


#include <libfprint/fprint.h>

typedef enum {
  NONE = 0,
  ENROLLING = 1,
  IDENTIFYING = 2
} SingleState;

class User;
class FPReader;


class FPReader {
 public:
  FPReader(fp_dev* device);
  void ChangeState(SingleState newstate);
  void UpdateState();

  void OpenCallback(int status);
  void EnrollStageCallback(int result, struct fp_print_data* print, struct fp_img* img);
  void EnrollStopCallback();
  void IdentifyCallback(int result, size_t match_offset, struct fp_img *img);
  void IdentifyStopCallback();

  int StartEnroll();
  int StopEnroll();
  int StartIdentify();
  int StopIdentify();

 //private:
  void AddUser(User*);

  SingleState state;
  SingleState next;

  std::vector<User*> users;
  fp_print_data** user_array;

  fp_dev* device;
};

class User {
 public:
  User(fp_print_data* fingerprint_, std::string username_);
  fp_print_data* print;
  std::string username;
};



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



#endif
