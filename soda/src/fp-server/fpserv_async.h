#ifndef FPSERV_ASYNC_H
#define FPSERV_ASYNC_H

#include <libfprint/fprint.h>

typedef enum {
  START_ENROLLING,
  STOP_ENROLLING
} Action;

typedef enum {
  ENROLLING,
  IDENTIFYING,
  NONE
} SingleState;


class FPReader {
 public:
  FPReader(fp_dev* device);
  void ChangeState(Action a);

  void OpenCallback(int status);
  void EnrollStageCallback(int result, struct fp_print_data* print, struct fp_img* img);
  void EnrollStopCallback();
  void IdentifyCallback(int result, size_t match_offset, struct fp_img *img);
  void IdentifyStopCallback();

  int StartEnroll();
  int StopEnroll();
  int StartIdentify();
  int StopIdentify();

 private:
  SingleState state;
  SingleState next;

  fp_dev* device;
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
