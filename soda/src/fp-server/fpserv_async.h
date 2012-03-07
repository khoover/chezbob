#ifndef FPSERV_ASYNC_H
#define FPSERV_ASYNC_H
#include <iostream>
#include <vector>

#include <servio.h>

#include <libfprint/fprint.h>

typedef enum {
  NONE = 0,
  WAITING = 1,
  ENROLLING = 2,
  IDENTIFYING = 3
} SingleState;

#define STATESTRING(var) \
  (var == IDENTIFYING ? "IDENTIFYING" : \
   var == ENROLLING ? "ENROLLING" : \
   var == WAITING ? "WAITING" : \
   "NONE")

class User;
class FPReader;


class FPReader {
 public:
  static void InitializeFP();

  FPReader();
  ~FPReader();

  // Sets the username for the next Enroll phase
  void SetUsername(std::string username);

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

  void SendGoodRead(User* u);
  void SendBadRead(std::string message);

  void SendLearnGood(User* u);
  void SendLearnBad(std::string message);

 //private:
  void AddUser(User*);

  // Opens the first device that libfprint sees
  bool OpenDevice();

  SingleState state;
  SingleState next;

  std::string enrollingUser;

  std::vector<User*> users;
  fp_print_data** user_array;

  fp_dev* device;

  static bool fp_initialized;
};

class User {
 public:
  User(fp_print_data* fingerprint_, std::string username_);
  fp_print_data* print;
  std::string username;
};

// Callbacks for the C function pointer API
void dev_open_cb(struct fp_dev* dev, int status, void *user_data);
void enroll_stage_cb(struct fp_dev *dev, int result, struct fp_print_data *print, struct fp_img *img, void *user_data);
void enroll_stop_cb(struct fp_dev *dev, void *user_data);
void identify_cb(struct fp_dev *dev, int result, size_t match_offset, struct fp_img *img, void *user_data);
void identify_stop_cb(struct fp_dev *dev, void *user_data);

#endif
