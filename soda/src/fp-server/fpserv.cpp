#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <signal.h>
#include <netinet/in.h>
#include <assert.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <sys/mman.h>

#include <FL/fl_draw.H>
#include <FL/Fl.H>
#include <FL/Fl_Window.H>
#include <FL/Fl_Box.H>
#include <FL/Fl_Button.H>
#include <FL/Fl_Double_Window.H>
//#include <FL/Fl_Value_Slider.H>
#include <FL/Fl_Image.H>
#include <FL/Fl_PNG_Image.H>

#define SCREEN_H  300
#define SCREEN_W  256

#include <VFinger.h>
#include <servio.h>

#define VGLOB
#include "fpserv.h"

/// main cycle counter
int cycle = 0;
// last time non-null image was displayed
int64 feat_last_time = 0;
// for feat_done, some extra info
char feat_done_msg[1024];
// decreased scale (1 = normal)
double descale;
// visiblity flag
int visible = 0;
// time of last visibility change
int64 vis_since=0;
// recognizer handle
HVFCONTEXT vfcont;
// window dimensions. do not set directly - use descale
//  external (including border)
int exwinw, exwinh;
//  FP window size
int fpwinw, fpwinh;
// config parameters: window top-left corner on screen
int winx, winy;
// if true, inverts the image
int win_invert = 1;
// auto-flags
int auto_show = 0;
int auto_hide = 0;
// min deviation to start acqusition
int dev_threshold = 10;
// capture delay, ms. set to 0 to disable capture
int capture_delay = 0;
// match captured fp against database? 0 = no, else - strictness
int capture_match = 60;
// how many minutiaes requered for a good acqusition?
int capture_minutiae = 10;
// message1 (unused)
char * message1 = 0;
// message2 (unused)
char * message2 = 0;
// feature-done messages
char * featmsg_ok = 0;
char * featmsg_fail = 0;
char * featmsg_nomatch = 0;
// memory lock whole process
int memlock_all = 0;
// matching levels
int thresh_match = 50;
int thresh_learn = 60;
// next db cleanup time
int64 next_db_cleanup = 0;
// if set to 1, disables the scanning
int disabled = 0;
// window color scheme
char * winc_bg    = strdup("#000000");
char * winc_fp    = strdup("#FF0000");
char * winc_brd1  = strdup("#808080");
char * winc_brd2  = strdup("#FF8080");
char * winc_feat1 = strdup("#FF0000");
char * winc_feat2 = strdup("#00FF00");
char * winc_feat3 = strdup("#FFFFFF");
// message settings
int win_ms_findex = FL_COURIER;
int win_ms_size   = 10;
char * win_ms_color = strdup("#808080");
// large message
int win_ml_findex = FL_HELVETICA | FL_BOLD;
char * win_ml_color = strdup("#FFFF00");
// image for the backgound
Fl_Image * win_image = 0;
char * win_image_name = strdup("");
// borders around fingerprint
int win_bx1 = 10;
int win_bx2 = 10;
int win_by1 = 10;
int win_by2 = 10;
// message pos
int mpos_x1 = 0;
int mpos_y1 = 20;
int mpos_x2 = 100;
int mpos_y2 = 130;

// message mode:  0 = uf-srings; 1 = debug strings; 2 = numbers only
int msg_mode = 0;
// fingerprint image maximum contrast: 0
int win_fpcontr = 1;;


class MyStatusBox: public Fl_Widget {
public:
  MyStatusBox(int x, int y, int w, int h) :
    Fl_Widget(x, y, w, h) {
  };
  virtual void draw();
};



int stop_num = 0;
void onsignal(int num) { 
  stop_num = num;
};

int had_pipe = 0;
void onpipe(int num) { 
  had_pipe = 1;
};


MyStatusBox * infoline = 0;
Fl_Button * bt_save = 0;
Fl_Window *window  = 0;



int win_image_set(void*, void*) {
  if (win_image) free(win_image);
  if (!*win_image_name) {
    win_image = 0;
    sio_write(SIO_DEBUG, "Freeing the background image");
    return 0;
  };
  win_image = new Fl_PNG_Image(win_image_name);
  sio_write(SIO_DEBUG, "Loaded png image, size %dx%d, c=%d d=%d ld=%d, name '%s'", 
	    win_image->w(), win_image->h(), win_image->count(), win_image->d(), win_image->ld(),
	    win_image_name);
  return 0;
};

int winprop_set(void*, void*) {
  if (descale<= 0) descale = 1;
  fpwinw = int(SCREEN_W / descale); 
  fpwinh = int(SCREEN_H / descale);  
  exwinw = fpwinw+win_bx1+win_bx2;
  exwinh = fpwinh+win_by1+win_by2;
  sio_write(SIO_DEBUG, "Window resized to (%dx%d), fp is (%dx%d)", exwinw, exwinh, fpwinw, fpwinh);
  if (window)   window  ->resize(winx, winy, exwinw,exwinh);
  if (infoline) infoline->resize(0, 0, exwinw, exwinh);
  return 0;
};

int winvisible_set(void*x=0, void*y = 0) {
  if (!window) return 0;
  if (window->shown() == (visible!=0)) return 0;
  if (!x) {
    sio_write(SIO_DATA, "SYS-SET\tFPSERV\tvisible\t\t%d", visible);
  };
  if (visible) {
    window->show();
  } else {
    window->hide();
  };
  vis_since = time64();
};


void idlefunc(void * arg) {

  if (disabled)	cycle ^= 1;
  else	cycle++;

  if (stop_num) {
    delete window;
    window = 0;
    return;
  };

  if (had_pipe) {
    had_pipe = 0;
    sio_write(SIO_WARN, "Caught and ignored SIG_PIPE");
  };
  
  //
  //       process messages
  //
  std::string str = "";
  int rrv ;
  while ((rrv = sio_read(str, 0)) > 0) {
    std::string arg = sio_field(str, 0);
    std::string arg1 = sio_field(str, 1);
    if (arg == "FP-PRETEND") {	  
      sio_write(SIO_ERROR, "No fake image code implemented");
    } else if (arg == "FP-PERSIST") {	  
      fpdata_persists(atoi(arg1.c_str()), sio_field(str, 2), sio_field(str, 3));
    } else if (arg == "FP-LEARN") {	  
      int rec[16];
      rec[10] = 0;

      for (int i=0; i<10; i++) {
	std::string a = sio_field(str, 1+i);
	rec[i] = atoi(a.c_str());
	if (rec[i] == 0) break;
      };

      std::string exinfo = "";
      int rv = fpdata_generalize(rec, exinfo);

      sio_write(SIO_DATA, "FP-LEARN-DONE\t%d\t%s\t%s\t%s",
		(rv>0) ? rv : 0,
		(rv > 0) ? "ok" : (rv == 0) ? "mismatch" : (rv == -2) ? "notfound" : "error",
		exinfo.c_str(),
		(rv > 0)   ? "Success" :
		(rv == 0)  ? "Fingerprints are too different" :
		(rv == -1) ? "There was a problem with database" :
		(rv == -2) ? "There was a problem with data retention" :
		(rv == -3) ? "There was a problem with fingerprint engine" :
		"There as an unknown problem"); 
    } else if (arg == "SYS-SET") {
      // do nothing
    } else if (arg == "FP-UNPERSIST") {	  
      fpdata_unpersist(atoi(arg1.c_str()));

    } else if (arg == "FP-LIST") {	  

      std::string arg2 = sio_field(str, 2);
      std::string arg3 = sio_field(str, 3);
      fpdata_list(arg1.c_str(), arg2.c_str(), arg3.c_str(), "");

    } else {
      sio_write(SIO_DEBUG, "unknown message: [%s] [%s] [%s]", arg.c_str(), arg1.c_str(), str.c_str());
    }
  };
  if (rrv < 0) {
    sio_write(SIO_DEBUG, "server died: %d/%d", rrv, errno);
    stop_num = -100 + rrv; // exit if server dies
  };  

  if (cycle == 5) {
    sio_write(SIO_DATA, "FP-READY");
  };

  //   clean up database
  if (next_db_cleanup < time64()) {
    fpdata_db_cleanup();
    next_db_cleanup = time64() + 600 * 1000LL * 1000LL;
  };
  
  //
  //       fetch fingerprint info unless image hold is active
  //	  
  if (fpr_idle_callback()) {
    // TODO: request redraw
    window->redraw();
  };

  int fps = fpr_get_guistate();

  if (fps > 0) {
    if (auto_show) visible = 1;
    feat_last_time = time64();
  } else {
    // we went invisible
    if (auto_hide && visible && feat_last_time) 
      if ((feat_last_time + 1000*auto_hide) < time64()) {
	visible = 0;
	feat_last_time = 0;
      };
  };


  winvisible_set();
  // infoline->redraw();
};


void memlock_set(void*, void*) {
  int rv = 0;
  if (memlock_all == 0) {
    rv = munlockall();
  } else {
    rv = mlockall(MCL_CURRENT | MCL_FUTURE);
    if (rv < 0) {
      memlock_all = 0;
      sio_setvar("memlock_all", "d", 0);
    };
  };
  if (rv >= 0) {
    sio_write(SIO_DEBUG, "mlockall call success (lock=%d)", memlock_all);
  } else {
    sio_write(SIO_WARN, "mlockall call failed (lock=%d, error=%d)", memlock_all, errno);
  };
};


void btnClick(Fl_Widget*, void*) {
  sio_write(SIO_DATA, "FP-BUTTON");
};


int main(int argc, char **argv) {

  // connect to server
  if (sio_open(argc, argv, "FPSERV", "1.34", "") < 0)
    exit(10);
  sio_write(SIO_DATA, "SYS-ACCEPT\tSYS-SET\tFP-");
  //skip over junk
  std::string str;
  while (sio_read(str, 300) > 0) {};


  // init fp library
  int rv = VFInitialize ();
  if (rv != VFE_OK) {
    sio_close(rv, "cannot init fingerpint library");
    exit(12);
  }
  vfcont = VFCreateContext();
  if (vfcont == 0) {
    sio_close(rv, "cannot use fingerpint library");
    exit(14);
  };

  fpdb_init();

  VFSetParameter(VFP_RETURNED_IMAGE, 2, vfcont); // mangle image? 0=not, 1=yes, 2=outline

  signal(SIGHUP, &onsignal); 
  signal(SIGINT, &onsignal);
  signal(SIGTERM, &onsignal);
  signal(SIGPIPE, &onpipe);
  signal(SIGALRM, SIG_IGN); 
  signal(SIGUSR1, SIG_IGN); 
  signal(SIGUSR2, SIG_IGN); 

  if (!fpr_init()) {
    sio_close(1000 + errno, "cannot open fingeprint reader");
    exit(11);
  };


  fpr_start_thread();

  descale = 0.5;

  winx = 0;
  winy = 0;

  fpwinw = exwinw = 100; 
  fpwinw = exwinh = 100; 


  sio_getvar("descale",       "DC+:f", winprop_set, &descale);
  sio_getvar("winx",          "DC+:d", winprop_set, &winx);
  sio_getvar("winy",          "DC+:d", winprop_set, &winy);
  sio_getvar("fpr_threshold", "D+:d", &dev_threshold);

  sio_getvar("disabled",      "D+:d", &disabled);
  sio_getvar("visible",       "D+:d", &visible);
  sio_getvar("win_invert",    "D+:d", &win_invert);
  sio_getvar("win_fpcontr",    "D+:d", &win_fpcontr);
  sio_getvar("win_colors",    "D+:sssssss", &winc_bg, &winc_fp, 
	     &winc_brd1, &winc_brd2, 
	     &winc_feat1, &winc_feat2, &winc_feat3);
  sio_getvar("win_msgsmall",   "D+:dsd", &win_ms_findex, &win_ms_color, &win_ms_size);
  sio_getvar("win_msglarge",   "D+:ds", &win_ml_findex, &win_ml_color);

  sio_getvar("win_imgfile",  "DC+:s", win_image_set, &win_image_name);
  sio_getvar("win_imgborders", "DC+:dddd", winprop_set, &win_bx1, &win_by1, &win_bx2, &win_by2);

  sio_getvar("auto_show",     "D+:d", &auto_show);
  sio_getvar("auto_hide",     "D+:d", &auto_hide);
  sio_getvar("capture_delay", "D+:d", &capture_delay);
  sio_getvar("capture_match", "D+:d", &capture_match);
  sio_getvar("capture_minutiae", "D+:d", &capture_minutiae);

  sio_getvar("thresh_match",  "D+:d", &thresh_match);
  sio_getvar("thresh_learn",  "D+:d", &thresh_learn);

  sio_getvar("memlock_all",   "DC+:d", memlock_set, &memlock_all);

  // need to dup since old will be freed on change
  message1 = strdup("");
  message2 = strdup("");
  sio_getvar("message1",      "D+:s", &message1);
  sio_getvar("message2",      "D+:s", &message2);
  sio_getvar("msg_mode",      "D+:d", &msg_mode);
  sio_getvar("msg_pos",       "D+:dddd", &mpos_x1, &mpos_y1, &mpos_x2, &mpos_y2);

  featmsg_ok      = strdup("OK");
  featmsg_fail    = strdup("FAILED");
  featmsg_nomatch = strdup("ACCEPTED");
  sio_getvar("done_msgs",     "D+:sss", &featmsg_ok, &featmsg_fail, &featmsg_nomatch);

  //Fl::add_idle(&idlefunc, 0);

  Fl::visual(FL_DOUBLE|FL_RGB);
  Fl::visual(FL_DOUBLE|FL_INDEX);
  window = new Fl_Double_Window(exwinw, exwinh);
  infoline = new MyStatusBox(0,0, exwinw, exwinh);
  //bt_save = new Fl_Button(0, winh, winw, 40, "TEST");
  //bt_save->box(FL_PLASTIC_DOWN_BOX);
  //bt_save->callback(&btnClick);
  window->end();

  window->show(argc, argv);
  //Fl::sync();

  winprop_set(0, 0);
  win_image_set(0, 0);

  Fl::wait();
  Fl::wait();
	
  Fl::set_font((Fl_Font)16, "-bitstream-lcars-medium-r-normal--0-0-0-0-p-0-iso8859-1");
  int count = Fl::set_fonts(NULL); //");
  sio_write(SIO_DEBUG, "add fonts: total=%d", count);
  /*
  for (int i=0; i<=count; i++ ){
    int attr = 0;
    const char * c1 = Fl::get_font_name((Fl_Font)i, &attr);
    if (c1) {
      sio_write(SIO_DEBUG, "font table[%d] = %s (%X)", i, c1, attr);
    };
  };
  */

  while (window && !stop_num) {
    Fl::wait(0.1); // main loop: 0.1 seconds
    idlefunc(0);
  };

  rv = stop_num;

  fpr_kill_thread();
  fpdb_close();
  fpr_cleanup();
  sio_close(rv, (char*)(window ? "termination" : "window closed"));
  return rv;
}


void color2comp(unsigned int color, int&r, int&g, int&b, int &a) {
  b = (color>>24)&0xFF;
  g = (color>>16)&0xFF;
  r = (color>> 8)&0xFF;
  a = 0xFF;
};

int str2color(char * msg) {
  int p = 0;
  if (!sscanf(msg, "#%x", &p)) 
    if (!sscanf(msg, "0x%x", &p)) 
      if (!sscanf(msg, "%d", &p)) 
	return 0; // no format
  return htonl(p); 
};

unsigned char * ndat = 0;

#define INTERP(val, valmax, min, max)    ((min) + (((val)*((max)-(min))) / ((valmax))))
void MyStatusBox::draw() {
  //fl_color(FL_YELLOW);
  //fl_rectf(0, 0, winw, winh);
  CFPImage * img;

  char bf[1024];

  // parse background color
  int bgc = str2color(winc_bg);
  int br, bg, bb, ba;
  color2comp(bgc, br, bg, bb, ba);
  Fl_Color flb = fl_rgb_color(br, bg, bb);
	
  
  if (flb != color()) {
    color(flb);
    ::window->color(flb);
    sio_write(SIO_DEBUG, "changing bgcolor to %X", bgc);
  };

  fl_color(flb);
  fl_rectf(0, 0, exwinw, exwinh);

  // no transparency - draw under
  if (win_image && (win_image->d() != 4))
    win_image->draw(0,0);


  img = fpr_get_image();
  if (img) { // if image is present, draw it

    unsigned char * ndat = img->data;
    int depth = 1;
    
    // 'win_invert' means 'apply alt color'
    // so if it is set, we convert image to 3-components
    if (win_invert) {
      int fr, fg, fb, fa;
      
      // allocate color
      color2comp(str2color(winc_fp), fr, fg, fb, fa);

      // allocate array
      depth = 3;
      int size = img->width * img->height;
      const unsigned  char * odat = ndat;
      ndat = (unsigned char*)malloc(size * depth + 1);
      
      // get max brightness
      int max = 255 - win_fpcontr;
      if (max > 254) max=254;
      for (int oi=0; oi<size; oi++) {
	if (odat[oi]<max) max=odat[oi];
      };
      max = 255 - max;
      // todo: rewrite loop to remove this condition
      assert(img->width == img->stride);
      // convert image
      for (int oi=0, ni=0; oi<size; oi++) {
	unsigned int col = 255 - odat[oi];

	if (col < 0) col = 0; 
	if (col > max) col = max;
	ndat[ni+0] = INTERP(col, max, br, fr);
	ndat[ni+1] = INTERP(col, max, bg, fg);
	ndat[ni+2] = INTERP(col, max, bb, fb);
	//ndat[ni+3] = INTERP(odat, fa, ba);
	ni+= depth;
      };
    };

    // conver to object
    Fl_RGB_Image * i1= new Fl_RGB_Image(ndat, img->width, img->height, depth, 0);
    Fl_Image * i2;
    // resize if needed
    if ((img->width == fpwinw) && (img->height == fpwinh)) {
      i2 = i1;
    } else {
      i2 = i1->copy(fpwinw, fpwinh);
      delete i1;
      i1 = 0;
    };
    // and draw it..
    i2->draw(win_bx1, win_by1);
    delete i2;

    if (ndat && (ndat != img->data)) { free(ndat); ndat = 0; };

    if (img->mincount) {
      // if we have minutea data, draw it too
      fl_font(FL_COURIER, 8);
      for (int i=0; i<img->mincount; i++) {
	switch (img->mindata[i].T) {
	case vfmtBifurcation:  fl_color(str2color(winc_feat1)); break;
	case vfmtEnd:          fl_color(str2color(winc_feat2)); break;
	default:              fl_color(str2color(winc_feat3)); break;
	};
	int x0 = int(img->mindata[i].X / descale) + win_bx1;
	int y0 = int(img->mindata[i].Y / descale) + win_by1;
	  
	fl_circle(x0, y0, 3);
	double len = 10 / descale;
	double ang = VFDirToRad(img->mindata[i].D);
	//if (mindata[i].T == vfmtBifurcation) len = -len;
	double ang2 = ang - VFDirToRad(img->mindata[i].C);
	//double ang2 = VFDirToRad(mindata[i].C);
	int x1 = int(x0 + len*cos(ang));
	int y1 = int(y0 + len*sin(ang));
	fl_line_style(FL_SOLID, 3, 0); 
	fl_line(x0, y0, x1, y1);
	//len = 0;
	//fl_line(x1, y1, int(x1 + len*cos(ang2)), int(y1+len*sin(ang2)));	  
	sprintf(bf, "%d:%d", img->mindata[i].C, 
		img->mindata[i].G);
	fl_draw(bf, x0+5, y0);
      };
    };
  };

  // with transparency - draw over
  if (win_image && (win_image->d()==4))
    win_image->draw(0,0);


  fl_font(win_ms_findex, win_ms_size);
  fl_color(str2color(win_ms_color));

  // do the number around the image
  if (1) {
    for (int i=0; i<4; i++) {
      int x = (i&1)?mpos_x2:mpos_x1;
      int y = (i&2)?mpos_y2:mpos_y1;
      switch (i) {
      case 0: sprintf(bf, "%d", cycle&1000); break;
      case 1: sprintf(bf, "%d", img ? img->featG : 0); break;
      case 2: sprintf(bf, "%d", img ? img->state : 0); break;
      case 3: sprintf(bf, "%d", img ? img->mincount: 0); break;		
      };
      int w=0, h=0;
      fl_measure(bf, w, h);
      if (!(i&1)) x -= w;
      fl_draw(bf, x, y);
    };
  };
  
  // if there is no background, do the border
  if (!win_image) {
    if (fpr_get_guistate() >= 5) {
      // thick dashed borden
      fl_color(str2color(winc_brd2));
      fl_line_style(FL_DASH, 8, 0); 
    } else {
      // thin solid border
      fl_color(str2color(winc_brd1));
      fl_line_style(FL_SOLID, 3, 0); 
    };
    fl_loop(0,0, 
	    exwinw-1, 0,
	    exwinw-1, exwinh-1,
	    0,        exwinh-1);
  };

  // check for large messagae
  char * msg = 0;
  switch (fpr_get_guistate()) {
  case FPS_LOWPOINTS: msg = "BAD IMAGE"; break;
  case FPS_MATCHES: msg = featmsg_ok; break;
  case FPS_NOMATCH: msg = featmsg_fail; break;
  case FPS_NOMATCH_BAD: msg = "FAILED"; break;
  case FPS_STORED: msg = featmsg_nomatch; break;
  };

  if (msg) {
    // draw large message if needed
    fl_color(str2color(win_ml_color));
    // find max font size by binary search
    int stfsize = 20;
    int stfset  = 32;
    int w, h;
    while (1) {
      fl_font(win_ml_findex, stfsize);
      w = 0; h =0;
      fl_measure(msg, w, h);
      // do 10% hirozontal margins
      if (((w+w/10)>=fpwinw) || (h>=fpwinh)) {
	stfsize -= stfset;
	if (stfset > 1) stfset = stfset / 2;
      } else {
	if (stfset <= 2) break; // search done
	stfsize += stfset;
      };
    };
    // draw it
    fl_draw(msg, win_bx1, win_by1, fpwinw, fpwinh, FL_ALIGN_CENTER);
  };


  if (img)
    fpr_release_image(img);
};

