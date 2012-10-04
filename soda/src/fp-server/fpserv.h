#ifndef __FPSERV_H__
#define __FPSERV_H__

#include <string>
#include <VFinger.h>

#ifndef VGLOB
#define VGLOB extern
#endif

//
//

extern int thresh_match;
extern HVFCONTEXT vfcont;


//   MAXIMUM image width/height
#define IMG_MAX_W     512
#define IMG_MAX_H     512


//
//   Reader Functions (fp_reader.cpp)
//

// fingerpint states, also [gui states]
// note: states with * will not appear in CPImage->state
#define FPS_EMPTY       0   // capture has not occured yet [no active image]
#define FPS_UNCAPTURED  5   // * [working on capturing]
#define FPS_UNPARSED   10   // image was not parsed [parsing image]
#define FPS_LOWPOINTS  20   // image had too few points, could not match [bad image]
#define FPS_CANMATCH   30   // image is ready to be matched to DB [matching in process]
#define FPS_NOMATCH    40   // image does not match
#define FPS_NOMATCH_BAD 45  // * [LOWPOINTS, but would no retry]
#define FPS_STORED     50   // image was not even matched, but was stored into database
#define FPS_MATCHES    60   // image matches


// image from fingerprint
class CFPImage {
  // internal data structures
  void * fpimg;

  // init/cleanup hardware-specific wars
  bool hw_init();
  bool hw_cleanup();

 public:
  // reference count
  int refcount;

  // image data
  int width;
  int height;
  int stride; // could be same or bigger than width
  int dpi;
  unsigned char * data;

  // fingerprint recognition data
  unsigned char featdata[VF_MAX_FEATURES_SIZE];
  int featsize;

  // feature details
  int featG;
  int mincount;
  int contrast;
  VFMinutia mindata[VF_MAX_MINUTIA_COUNT];

  CFPImage();
  ~CFPImage();

  // image state (FPS_XXX constant)
  int state;
  // when FPS_MATCHES or FPS_STORED, image id; else 0
  int fpid;
  // for matches: simularity, finger, uid
  int fprel;
  std::string uid;
  std::string finger;


  // acquire image from scanner; true = success
  bool acquire();
  // prepare image for recognizing; true = success
  bool prepare();
  // match image; true if matches
  bool match();
  // store image if stroign is enabled; true = success
  bool store();

  // save image: data with .pgm suffix, features with .txt suffix
  bool saveData(std::string & prefix);
};

// true = success
// fpr reader device init
bool fpr_init();
// fpr reader device cleanup
bool fpr_cleanup();

// start/stop main image  processing thread
bool fpr_start_thread();
bool fpr_kill_thread();

// GUI: get image to draw, or NULL if nothing to draw
// image is locked - do not forget to release it
CFPImage * fpr_get_image();
void fpr_release_image(CFPImage * img);

// GUI: call from mail loop callback
// RV: true if need image repaint
//     false otherwise
bool fpr_idle_callback();


// GUI: get state
//  set FPS_ constats for info
int fpr_get_guistate();

//
//   DB functions (fp_db.cpp)
//

// init database. exit() if failed
void  fpdb_init();
void fpdb_close();

// save data to database. life is 0 for short-life, 1 for long life
// RV is fpid
int fpdata_save(unsigned char * featdata, int  featsize, int life);

// match FP against database
// input: features
// output: uid from database
//         match reliability
// RV:     match fpid (from database)
//         0 not found, -1 error
int  fpdata_match(unsigned char * featdata, int featsize,
				  std::string & uid, std::string & finger, int & rel);


// store UID in fp's entry, and mark it persistend and matchable.
// input:  fpid,  uid, finger
// output: -1 for error, >0 for success
int  fpdata_persists(int fpid, const std::string uid, const std::string finger);

// try to generalize one or more fingerpints
// input: array of ints, 0-terminates
// output: extra match info
// RV:   >0  - match went fine, this is the fpid
//        0  - values did not match
//       -1  - mysql error
//       -2  - some input was not found
//       -3  - some other error
int  fpdata_generalize(int * fpid_in, std::string& exinfo);

// clean up database by deleting old records
// called every 5 minutes
int  fpdata_db_cleanup();

// unpersists a specific record (and clears its matchable flag)
int fpdata_unpersist(int fpid);

// handle FP-LIST command
int fpdata_list(const char* queryid, const char * mode, const char * arg1, const char* arg2);


#endif
