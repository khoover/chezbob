#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <sys/mman.h>
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>
#include "fpserv.h"
#include <servio.h>


// private prototypes


//
//
//                   HARDWARE-DEPENDEND AREA (FPS2000)
//
//

#ifdef READER_DPFP

extern "C" {
#include <dpfp.h>
};

struct dpfp_dev * fp_dev;
static int fpr_hw_mode;

bool fpr_acquire_mode(bool acquire);

bool fpr_hw_init() {
  dpfp_init();
  fp_dev = dpfp_open();
  if (!fp_dev) {
    sio_write(SIO_WARN, "dpfp_open failed: errno=%d", errno);
    return false;
  };
  fpr_hw_mode = -1;
  if (!fpr_acquire_mode(false)) {
    sio_write(SIO_WARN, "fpr_acquire_mode failed: errno=%d", errno);
    return false;
  };
  return true;
};

// image init
bool CFPImage::hw_init() {
  fpimg = (void*)dpfp_fprint_alloc();
  width = DPFP_IMG_WIDTH;
  height = DPFP_IMG_HEIGHT;
  stride = width;
  data = ((dpfp_fprint*)fpimg)->data;
  dpi = 512;
  return true;
};

// image acquire
bool CFPImage::acquire() {
  if (dpfp_capture_fprint(fp_dev, ((dpfp_fprint*)fpimg)) < 0)
    return false;

  unsigned int total = 0;
  // the image is inverted
  for (unsigned int i=0; i< (DPFP_IMG_WIDTH*DPFP_IMG_HEIGHT); i++) {
    total += data[i];
    data[i] = (255 - data[i]);
  };
  // since lower limit is 0...
  contrast = total / (DPFP_IMG_WIDTH*DPFP_IMG_HEIGHT);

  // .. and upside-down
  for (unsigned int y1=0, y2=(height-1); y1 < y2; y1++, y2--)
    for (unsigned int x=0; x<width; x++) {
      unsigned char c = data[ x + y1 * stride ];
      data[ x + y1 * stride ] = data[ width-1-x + y2 * stride ];
      data[ width-1-x + y2 * stride ] = c;
    };

  state = FPS_UNPARSED;
  return true;
};

// image cleanup
bool CFPImage::hw_cleanup() {
  dpfp_fprint_free(((dpfp_fprint*)fpimg));
  fpimg = 0;
  return true;
};

bool fpr_hw_cleanup() {
  dpfp_close(fp_dev);
  return true;
};


// set wait/scan mode; arg=true --> start getting images
bool fpr_acquire_mode(bool acquire) {
  int m = acquire ? DPFP_MODE_SEND_FINGER : DPFP_MODE_AWAIT_FINGER_ON;
  if (m == fpr_hw_mode)
    return true;
  if (dpfp_set_mode(fp_dev, m) < 1) {
    return false;
  };
  dpfp_set_edge_light(fp_dev, acquire ? 255 : 0);
  fpr_hw_mode = m;
  return true;
};

// 1 - finger
// 0 - timeout
// -1 - failure
int fpr_wait_finger(int timeout) {
  int r = dpfp_await_finger_on_timeout(fp_dev, (timeout-1)/1000 + 1);
  return r;
};

#endif

//
//
//                   CFPImage support classes
//
//

CFPImage::CFPImage() {
  refcount = 1;
  featsize = 0;
  featG = 0;
  mincount = 0;
  state = FPS_EMPTY;
  uid = "";
  finger = "";
  fpid = 0;
  fprel = 0;
  hw_init();
};

CFPImage::~CFPImage() {
  hw_cleanup();
};


pthread_mutex_t gui_mutex = PTHREAD_ERRORCHECK_MUTEX_INITIALIZER_NP;
pthread_mutex_t servio_mutex = PTHREAD_ERRORCHECK_MUTEX_INITIALIZER_NP;

// servIO lock/unlock functions
int servio_locking_lock(void* arg) {
  int i = pthread_mutex_lock(&servio_mutex);
  if (i) {
    fprintf(stderr, "FATAL: servio mutex lock failure, code %d\n", i);
    exit(2);
  };
  return 0;
};

int servio_locking_unlock(void* arg) {
  int i = pthread_mutex_unlock(&servio_mutex);
  if (i) {
    fprintf(stderr, "FATAL: servio mutex unlock failure, code %d\n", i);
    exit(2);
  };

  return 0;
};

// global init
bool fpr_init() {
  sio_register_lock(servio_locking_lock, servio_locking_unlock, 0);
  if (!fpr_hw_init())
    return false;
  return true;
};

// global cleanup
bool fpr_cleanup() {
  fpr_hw_cleanup();
  return true;
};

extern int dev_threshold;  // unused
extern int capture_delay;
extern int capture_match;
extern int capture_minutiae;


// prepare finger for matching
bool CFPImage::prepare() {

  featsize = sizeof(featdata);
  assert(width == stride);
  if (VFExtract(width, height, data, dpi,
                (unsigned char*)featdata, (unsigned long*)&featsize, vfcont) < 0) {
    featsize = 0;
    featG = 0;
    mincount = 0;
    state = FPS_LOWPOINTS;
    return false;
  };

  featG = VFFeatGetG(featdata);
  mincount = VFFeatGetMinutiaCount(featdata);
  VFFeatGetMinutiae(featdata, mindata);

  state = (mincount > capture_minutiae) ? FPS_CANMATCH: FPS_LOWPOINTS;
  return true;
};


bool CFPImage::match() {

  //feat_done_msg[0] = 0;
  // save_image_data();
  if (capture_match) {
    fpid = fpdata_match(featdata, featsize, uid, finger, fprel);
  } else {
    fpid = 0;
  };

  if (fpid > 0) {
    state = FPS_MATCHES;
    sio_write(SIO_DEBUG, "FP matched %d, uid '%s', finger '%s', rel %d",
              fpid, uid.c_str(), finger.c_str(), fprel);
  } else {
    // always save
    state = capture_match ? FPS_NOMATCH : FPS_STORED;
    if (fprel) {
      sio_write(SIO_DEBUG, "FP (min=%d, contr=%d) was almost uid '%s', finger '%s', rel %d/%d",
                mincount, contrast, uid.c_str(), finger.c_str(), fprel, capture_match);
    } else if (capture_match) {
      sio_write(SIO_DEBUG, "FP (min=%d, contr=%d) was unrecognizeable", mincount, contrast);
    } else {
      sio_write(SIO_DEBUG, "FP (min=%d, contr=%d) was not matched" , mincount, contrast);
    };
  };

  return (state == FPS_MATCHES);
};

bool CFPImage::store() {
  if ((fpid == 0) && (state == FPS_NOMATCH || state == FPS_STORED)) {
    fpid = fpdata_save(featdata, featsize, 0);
  };
};


// "/dev/shm/fpserv_last"
bool CFPImage::saveData(std::string & prefix) {
  FILE * f;
  std::string fname = prefix + ".pgm";
  f = fopen(fname.c_str(), "wb");
  assert(width == stride);
  if (f) {
    fprintf(f, "P5 %d %d 255\n", width,  height);
    fwrite(data, 1, width * height, f);
    fclose(f);
  };

  fname = prefix + ".txt";
  f = fopen(fname.c_str(), "wb");
  if (f) {
    fprintf(f, "G=%d\n", featG);
    fprintf(f, "FEATURE START\n");
    for (int i=0; i<mincount; i++) {
      fprintf(f, " %s Pos=(%d,%d) D=%d,%d C=%d,%d G=%d\n",
              (mindata[i].T==vfmtBifurcation) ? "BIF":
              (mindata[i].T==vfmtEnd) ? "END": "OTH",
              mindata[i].X, mindata[i].Y,
              mindata[i].D, VFDirToDeg((int)mindata[i].D),
              mindata[i].C, VFDirToDeg((int)mindata[i].C),
              mindata[i].G);
    };
    fprintf(f, "FEATURE END\n");

    fclose(f);
  };
};


//
//
//                   Main Loop and State Vars
//
//

extern bool disabled;
// set to non-zero to kill main thread
extern int stop_num;


static bool thread_stop = false;
static int gui_state = 0;
static CFPImage * gui_img;
static bool refresh_gui = false;

CFPImage * fpr_get_image() {
  CFPImage * rv =0;
  pthread_mutex_lock(&gui_mutex);
  rv = gui_img;
  if (rv)
    rv->refcount++;
  pthread_mutex_unlock(&gui_mutex);
  return rv;
};

void fpr_release_image(CFPImage * img) {
  pthread_mutex_lock(&gui_mutex);
  img->refcount--;
  if (img->refcount == 0)
    delete img;
  pthread_mutex_unlock(&gui_mutex);
};

int fpr_get_guistate() {
  return gui_state;
};

static int set_gui_state(int s, CFPImage * img = (CFPImage*)-1) {
  gui_state = s;

  pthread_mutex_lock(&gui_mutex);
  if ((img != (CFPImage*)-1) &&
      (img != gui_img)) {
    // delete old image
    if (gui_img) {
      gui_img->refcount--;
      if (gui_img->refcount == 0)
        delete gui_img;
      gui_img = 0;
    };
    // set new image
    gui_img = img;
    if (gui_img)
      gui_img->refcount++;
  };
  pthread_mutex_unlock(&gui_mutex);

  refresh_gui = true;
};

// pthread_start function
void* fpr_main(void * dummy) {
  while (!thread_stop) {
    set_gui_state(FPS_EMPTY, NULL);
    fpr_acquire_mode(false);
    int r = fpr_wait_finger(500);
    if (r < 0) {
      stop_num = 3000 - r;
      break;
    };
    // no finger
    if (r == 0)
      continue;
    CFPImage * img = 0;
    set_gui_state(FPS_UNCAPTURED, NULL);

    // start capturing
    fpr_acquire_mode(true);
    for (int i=0; i<3; i++) {
      if (thread_stop) break;
      if (img)
        fpr_release_image(img);

      img = new CFPImage();
      set_gui_state(FPS_UNCAPTURED);

      if (!img->acquire()) {
        fpr_release_image(img);
        break;
      };
      set_gui_state(FPS_UNPARSED);

      if (!img->prepare()) {
        set_gui_state(FPS_EMPTY, 0);
        fpr_release_image(img);
        img = 0;
        break;
      };

      set_gui_state(img->state, img);

      if (img->state == FPS_CANMATCH) {
        if (img->match()) {
          set_gui_state(img->state, img); // match
          break;
        };
      } else {
        set_gui_state(FPS_LOWPOINTS, img);
      };
    };

    if (img) {
      if (img->state == FPS_LOWPOINTS) {
        set_gui_state(FPS_NOMATCH_BAD, img);
      } else {
        // we had at least one satisfactory image
        set_gui_state(img->state, img);

        if (img->state == FPS_MATCHES) {
          sio_write(SIO_DATA, "FP-GOODREAD\t%d\t%s\t%s\t%d", img->fpid, img->uid.c_str(), img->finger.c_str(), img->fprel);
        } else {
          img->store();
          sio_write(SIO_DATA, "FP-BADREAD\t%d", img->fpid);
        };
      };
      fpr_release_image(img);
      // TODO: fix this somehow!!!
      sleep(1);
    };
  };
};

pthread_t fp_thread;

bool fpr_start_thread() {
  thread_stop = false;
  //fpr_main(0);
  int i = pthread_create(&fp_thread, 0, fpr_main, NULL);
  if (!i) return true;
  stop_num = 4000 + i;
  return false;
};

bool fpr_kill_thread() {
  int rv;
  thread_stop = true;
  pthread_join(fp_thread, (void**)&rv);
};



bool fpr_idle_callback() {
  bool rv = false;
  if (refresh_gui) {
    rv = true;
    refresh_gui = false;
  };
  return rv;
};






