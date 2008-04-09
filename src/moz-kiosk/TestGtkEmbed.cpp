/* ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 *
 * The Original Code is mozilla.org code.
 *
 * The Initial Developer of the Original Code is
 * Christopher Blizzard. Portions created by Christopher Blizzard are Copyright (C) Christopher Blizzard.  All Rights Reserved.
 * Portions created by the Initial Developer are Copyright (C) 2001
 * the Initial Developer. All Rights Reserved.
 *
 * Contributor(s):
 *   Christopher Blizzard <blizzard@mozilla.org>
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 2 or later (the "GPL"), or
 * the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 *
 * ***** END LICENSE BLOCK ***** */

#define MOZILLA_INTERNAL_API 


#include <gtk/gtk.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// for low-level stuff


#include <widget/nsEvent.h>
#include <nsCOMPtr.h>
#include <nsIWebBrowser.h>
#include <nsIDOMWindow.h>
#include <dom/nsIScriptGlobalObject.h>
//#include <content/nsContentUtils.h>
//#include <string/nsString.h>
//#include <js/jsapi.h>
#include <nsIScriptContext.h>
#include <nsReadableUtils.h>

// mozilla specific headers
#include <dom/nsIDOMKeyEvent.h>
#include <nsIDOMMouseEvent.h>
#include <nsIDOMUIEvent.h>
#include <nspr/prenv.h>

#include <gtkmozembed.h>

#ifdef NS_TRACE_MALLOC
#include "nsTraceMalloc.h"
#endif

#ifdef MOZ_JPROF
#include "jprof.h"
#endif

#include <string>
typedef std::string string;

#include <servio.h>

// secret header..
extern "C"
void gtk_moz_embed_get_nsIWebBrowser  (GtkMozEmbed *embed, nsIWebBrowser **retval);

typedef struct _TestGtkBrowser {
  GtkWidget  *topLevelWindow;
  GtkWidget  *topLevelVBox;
  GtkWidget  *mozEmbed;
  char * url;
  //const char *statusMessage;
  //  int         loadPercent;
  //int         bytesLoaded;
  // int         maxBytesLoaded;
  //char       *tempMessage;
} TestGtkBrowser;

// requested location
char * req_loc;


// main browser window
TestGtkBrowser * browser;

static TestGtkBrowser *new_gtk_browser    (guint32 chromeMask);
static void            set_browser_visibility (TestGtkBrowser *browser,
					       gboolean visibility);
static gboolean delete_cb          (GtkWidget *widget, GdkEventAny *event,
                                    TestGtkBrowser *browser);
static void     destroy_cb         (GtkWidget *widget,
                                    TestGtkBrowser *browser);

// callbacks from the widget
static void location_changed_cb  (GtkMozEmbed *embed, TestGtkBrowser *browser);
static void title_changed_cb     (GtkMozEmbed *embed, TestGtkBrowser *browser);
static void load_started_cb      (GtkMozEmbed *embed, TestGtkBrowser *browser);
static void load_finished_cb     (GtkMozEmbed *embed, TestGtkBrowser *browser);
static void net_state_change_cb  (GtkMozEmbed *embed, gint flags,
				  guint status, TestGtkBrowser *browser);
static void net_state_change_all_cb (GtkMozEmbed *embed, const char *uri,
				     gint flags, guint status,
				     TestGtkBrowser *browser);
static void progress_change_cb   (GtkMozEmbed *embed, gint cur, gint max,
				  TestGtkBrowser *browser);
static void progress_change_all_cb (GtkMozEmbed *embed, const char *uri,
				    gint cur, gint max,
				    TestGtkBrowser *browser);
static void link_message_cb      (GtkMozEmbed *embed, TestGtkBrowser *browser);
static void js_status_cb         (GtkMozEmbed *embed, TestGtkBrowser *browser);
static void new_window_cb        (GtkMozEmbed *embed,
				  GtkMozEmbed **retval, guint chromemask,
				  TestGtkBrowser *browser);
static void visibility_cb        (GtkMozEmbed *embed, 
				  gboolean visibility,
				  TestGtkBrowser *browser);
static void destroy_brsr_cb      (GtkMozEmbed *embed, TestGtkBrowser *browser);
static gint open_uri_cb          (GtkMozEmbed *embed, const char *uri,
				  TestGtkBrowser *browser);
static void size_to_cb           (GtkMozEmbed *embed, gint width,
				  gint height, TestGtkBrowser *browser);
static gint dom_key_down_cb      (GtkMozEmbed *embed, nsIDOMKeyEvent *event,
				  TestGtkBrowser *browser);
static gint dom_key_press_cb     (GtkMozEmbed *embed, nsIDOMKeyEvent *event,
				  TestGtkBrowser *browser);
static gint dom_key_up_cb        (GtkMozEmbed *embed, nsIDOMKeyEvent *event,
				  TestGtkBrowser *browser);
static gint dom_mouse_down_cb    (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
				  TestGtkBrowser *browser);
static gint dom_mouse_up_cb      (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
				  TestGtkBrowser *browser);
static gint dom_mouse_click_cb   (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
				  TestGtkBrowser *browser);
static gint dom_mouse_dbl_click_cb (GtkMozEmbed *embed, 
				  nsIDOMMouseEvent *event,
				  TestGtkBrowser *browser);
static gint dom_mouse_over_cb    (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
				  TestGtkBrowser *browser);
static gint dom_mouse_out_cb     (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
				  TestGtkBrowser *browser);
static gint dom_activate_cb      (GtkMozEmbed *embed, nsIDOMUIEvent *event,
				  TestGtkBrowser *browser);
static gint dom_focus_in_cb      (GtkMozEmbed *embed, nsIDOMUIEvent *event,
				  TestGtkBrowser *browser);
static gint dom_focus_out_cb     (GtkMozEmbed *embed, nsIDOMUIEvent *event,
				  TestGtkBrowser *browser);


// RV: < 0 = error
//       0 = undef
//       1 = value in res
int ns_obj_action(TestGtkBrowser *browser, int type, std::string& res,  const char * arg1, const char * arg2=0) {		
  nsCOMPtr<nsIWebBrowser> iwb;

  gtk_moz_embed_get_nsIWebBrowser(GTK_MOZ_EMBED(browser->mozEmbed), getter_AddRefs(iwb));
  if (!iwb) return -1;
  
  nsCOMPtr<nsIDOMWindow> dom;
  iwb->GetContentDOMWindow(getter_AddRefs(dom));
  if (!dom) return -2;

  int rv = 0;

  if (type == 1) {
	nsCOMPtr<nsIScriptGlobalObject> globscript = do_QueryInterface(dom);
	if (!globscript) return -3;
	
	// TODO"    (dont_AddRef(,,,.)) ?
	nsCOMPtr<nsIScriptContext> iscontext = globscript->GetContext();
	if (!iscontext) return -4;

	//JSContext* cx = (JSContext*)(iscontext->GetNativeContext());

	if (arg2) {
	  dom->SetName(NS_ConvertASCIItoUCS2(arg2));
	};

	nsAutoString result;
	nsresult rv;
	//nsAutoGCRoot root(&result, &rv);

	JSObject * scriptObject = 0;
	//holder->GetJSObject(&scriptObject);
	PRBool undefined;
	//nsAString code = ;
	rv = iscontext->EvaluateString
	  (NS_ConvertASCIItoUCS2(arg1), scriptObject, nsnull, 
	   nsnull, 0, nsnull, &result, &undefined);

	// c: EvaluateString(nsAString_internal&, JSObject*&, int,           const char[8], int,         int, void*, PRBool*)'
	// f: EvaluateString(nsAString_internal&, void*,      nsIPrincipal*, char*,         unsigned int, const char*,  nsAString_internal*, PRBool*) <near match>

	if (NS_FAILED(rv))
	  return -5;

	if (!undefined) {
	  char * c = ToNewCString(result);
	  res = string(c);
	  delete[] c;
	  rv = 1;
	};
  } else return -1000;

  return rv;
};


static gboolean idle_cb (gpointer data)
{
  while (1) {
	string msg;
	int rv = sio_read(msg, 3); // 3 ms latency on idle...
	if (rv < 0) gtk_main_quit();
	if (rv <= 0) break;
	std::string mtype = sio_field(msg, 0);
	std::string arg1 = sio_field(msg, 1);
	std::string arg2 = sio_field(msg, 2);
	if (mtype == "MOZ-GO-BACK") {
	  gtk_moz_embed_go_back(GTK_MOZ_EMBED(browser->mozEmbed));
	} else if (mtype == "MOZ-STOP") {
	  gtk_moz_embed_stop_load(GTK_MOZ_EMBED(browser->mozEmbed));
	} else if (mtype == "MOZ-FORWARD") {
	  gtk_moz_embed_go_forward(GTK_MOZ_EMBED(browser->mozEmbed));
	} else if (mtype == "MOZ-RELOAD") {
	  int nocache = arg1.length() && (arg1 != "0");
	  gtk_moz_embed_reload(GTK_MOZ_EMBED(browser->mozEmbed),
						   nocache ?
						   GTK_MOZ_EMBED_FLAG_RELOADBYPASSCACHE : 
						   GTK_MOZ_EMBED_FLAG_RELOADNORMAL);
	} else if (mtype == "MOZ-SHOW") {
	  int vis = arg1.length() && (arg1 != "0");
	  set_browser_visibility (browser, vis);
	} else if (mtype == "MOZ-OPEN") {
	  if (strncmp(arg1.c_str(), "text:", 5)==0) {
		gtk_moz_embed_render_data(GTK_MOZ_EMBED(browser->mozEmbed), 
								  arg1.data()+5, arg1.length()-5, "file://", "text/html");
	  } else { 
		gtk_moz_embed_load_url(GTK_MOZ_EMBED(browser->mozEmbed), arg1.c_str());
	  };
	} else if (mtype == "MOZ-RENDER-STRING") {
	  // args: data-to-render base-url content-type
	  string base = sio_field(msg, 2);
	  if (base == "") base = "file://";
	  string type = sio_field(msg, 3);
	  if (type == "") type = "text/html";
	  gtk_moz_embed_render_data(GTK_MOZ_EMBED(browser->mozEmbed), arg1.data(), arg1.length(), base.c_str(), type.c_str());
	} else if (mtype == "MOZ-JAVASCRIPT") {
	  string res;
	  int rv = ns_obj_action(browser, 1, res, arg1.c_str(), arg2.c_str());
	  if (rv < 0) {
		sio_write(SIO_DATA, "MOZ-JAVASCRIPT-DONE\t%s\t%d", "error", rv);
	  } else {
		sio_write(SIO_DATA, "MOZ-JAVASCRIPT-DONE\t%s\t%s", (rv==0)?"undef":"ok", res.c_str());
	  };
	} else if (mtype == "MOZ-OPEN-FRAME") {
	  string jsc = "frames[";
	  if (arg1.find_first_not_of("1234567890") >= 0)
		jsc = jsc + "\"" + arg1 + "\"";
	  else
		jsc = jsc + arg1;
	  jsc = jsc + "].location=window.name;";
	  string res;
	  int rv = ns_obj_action(browser, 1, res, jsc.c_str(), arg2.c_str());
	  if (rv < 0) {
		sio_write(SIO_WARN, "OPEN-FRAME failed\t%s\t%s\t%d", jsc.c_str(), arg2.c_str(), rv);
	  } else {
		sio_write(SIO_DEBUG, "OPEN-FRAME OK\t%s\t%s\t%s", jsc.c_str(), arg2.c_str(), res.c_str());
	  };
	} else {
	  sio_write(SIO_DEBUG, "Unknown command:\t%s", msg.c_str());
	};
  };
  return TRUE;
};

// callbacks from the singleton object
static void new_window_orphan_cb (GtkMozEmbedSingle *embed,
				  GtkMozEmbed **retval, guint chromemask,
				  gpointer data);



int reqloc_reload(void*, void*) {
  gtk_moz_embed_load_url(GTK_MOZ_EMBED(browser->mozEmbed), req_loc);
  return 0;
};

int
main(int argc, char **argv)
{
#ifdef NS_TRACE_MALLOC
  argc = NS_TraceMallocStartupArgs(argc, argv);
#endif


  if (sio_open(argc, argv, "MOZ-KIOSK", "1.10")) return 8;
  sio_write(SIO_DATA, "SYS-ACCEPT\tMOZ-\tSYS-SET|MOZ-KIOSK|");

  gtk_set_locale();
  if (!gtk_init_check(&argc, &argv)) {
	sio_close(1, "Cannot init GTK");
	exit(1);
  };

#ifdef MOZ_JPROF
  setupProfilingStuff();
#endif

  char *home_path;
  char *full_path;
  home_path = PR_GetEnv("HOME");
  if (!home_path) {
    fprintf(stderr, "Failed to get HOME\n");
    exit(1);
  }
  
  full_path = g_strdup_printf("%s/%s", home_path, ".moz-kiosk");

  gtk_moz_embed_set_profile_path(full_path, "ff-profile");

  browser = new_gtk_browser(GTK_MOZ_EMBED_FLAG_DEFAULTCHROME);

  // set our minimum size
  gtk_widget_set_usize(browser->mozEmbed, 800, 600);
  set_browser_visibility(browser, TRUE);

  req_loc = strdup((argc>1) ? argv[1] : "http://localhost/lh/start");
  sio_getvar("location", "CD+:s", reqloc_reload, &req_loc);
  reqloc_reload(0,0);
	 

  // get the singleton object and hook up to its new window callback
  // so we can create orphaned windows.

  GtkMozEmbedSingle *single;

  single = gtk_moz_embed_single_get();
  if (!single) {
    fprintf(stderr, "Failed to get singleton embed object!\n");
    exit(1);
  }

  gtk_idle_add (&idle_cb, NULL);

  gtk_signal_connect(GTK_OBJECT(single), "new_window_orphan",
		     GTK_SIGNAL_FUNC(new_window_orphan_cb), NULL);

  gtk_main();
  sio_close();
}

static TestGtkBrowser *
new_gtk_browser(guint32 chromeMask)
{
  guint32         actualChromeMask = chromeMask;
  //TestGtkBrowser *browser = 0;

  if (browser)
	sio_write(SIO_WARN, "Opening new window, mask %X", chromeMask);

  browser = g_new0(TestGtkBrowser, 1);

  browser->url = strdup("");


  if (chromeMask == GTK_MOZ_EMBED_FLAG_DEFAULTCHROME)
    actualChromeMask = GTK_MOZ_EMBED_FLAG_ALLCHROME;
  

  // create our new toplevel window
  browser->topLevelWindow = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  // new vbox
  browser->topLevelVBox = gtk_vbox_new(FALSE, 0);
  // add it to the toplevel window
  gtk_container_add(GTK_CONTAINER(browser->topLevelWindow),
		    browser->topLevelVBox);


  // create our new gtk moz embed widget
  browser->mozEmbed = gtk_moz_embed_new();
  gtk_box_pack_start(GTK_BOX(browser->topLevelVBox), browser->mozEmbed,
                     TRUE, // expand
                     TRUE, // fill
                     0);   // padding

  // catch the destruction of the toplevel window
  gtk_signal_connect(GTK_OBJECT(browser->topLevelWindow), "delete_event",
                     GTK_SIGNAL_FUNC(delete_cb), browser);


  // hook up the location change to update the urlEntry
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "location",
		     GTK_SIGNAL_FUNC(location_changed_cb), browser);
  // hook up the title change to update the window title
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "title",
		     GTK_SIGNAL_FUNC(title_changed_cb), browser);
  // hook up the start and stop signals
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "net_start",
		     GTK_SIGNAL_FUNC(load_started_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "net_stop",
		     GTK_SIGNAL_FUNC(load_finished_cb), browser);
  // hook up to the change in network status
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "net_state",
		     GTK_SIGNAL_FUNC(net_state_change_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "net_state_all",
		     GTK_SIGNAL_FUNC(net_state_change_all_cb), browser);
  // hookup to changes in progress
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "progress",
		     GTK_SIGNAL_FUNC(progress_change_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "progress_all",
		     GTK_SIGNAL_FUNC(progress_change_all_cb), browser);
  // hookup to changes in over-link message
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "link_message",
		     GTK_SIGNAL_FUNC(link_message_cb), browser);
  // hookup to changes in js status message
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "js_status",
		     GTK_SIGNAL_FUNC(js_status_cb), browser);
  // hookup to see whenever a new window is requested
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "new_window",
		     GTK_SIGNAL_FUNC(new_window_cb), browser);
  // hookup to any requested visibility changes
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "visibility",
		     GTK_SIGNAL_FUNC(visibility_cb), browser);
  // hookup to the signal that says that the browser requested to be
  // destroyed
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "destroy_browser",
		     GTK_SIGNAL_FUNC(destroy_brsr_cb), browser);
  // hookup to the signal that is called when someone clicks on a link
  // to load a new uri
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "open_uri",
		     GTK_SIGNAL_FUNC(open_uri_cb), browser);
  // this signal is emitted when there's a request to change the
  // containing browser window to a certain height, like with width
  // and height args for a window.open in javascript
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "size_to",
		     GTK_SIGNAL_FUNC(size_to_cb), browser);
  // key event signals
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_key_down",
		     GTK_SIGNAL_FUNC(dom_key_down_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_key_press",
		     GTK_SIGNAL_FUNC(dom_key_press_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_key_up",
		     GTK_SIGNAL_FUNC(dom_key_up_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_mouse_down",
		     GTK_SIGNAL_FUNC(dom_mouse_down_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_mouse_up",
		     GTK_SIGNAL_FUNC(dom_mouse_up_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_mouse_click",
		     GTK_SIGNAL_FUNC(dom_mouse_click_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_mouse_dbl_click",
		     GTK_SIGNAL_FUNC(dom_mouse_dbl_click_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_mouse_over",
		     GTK_SIGNAL_FUNC(dom_mouse_over_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_mouse_out",
		     GTK_SIGNAL_FUNC(dom_mouse_out_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_activate",
		     GTK_SIGNAL_FUNC(dom_activate_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_focus_in",
		     GTK_SIGNAL_FUNC(dom_focus_in_cb), browser);
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "dom_focus_out",
		     GTK_SIGNAL_FUNC(dom_focus_out_cb), browser);
  // hookup to when the window is destroyed
  gtk_signal_connect(GTK_OBJECT(browser->mozEmbed), "destroy",
					 GTK_SIGNAL_FUNC(destroy_cb), browser);
  
  // set the chrome type so it's stored in the object
  gtk_moz_embed_set_chrome_mask(GTK_MOZ_EMBED(browser->mozEmbed),
				actualChromeMask);

  return browser;
}

void
set_browser_visibility (TestGtkBrowser *browser, gboolean visibility)
{
  if (!visibility)
  {
    gtk_widget_hide(browser->topLevelWindow);
    return;
  }
  
  gtk_widget_show(browser->mozEmbed);
  gtk_widget_show(browser->topLevelVBox);
  gtk_widget_show(browser->topLevelWindow);
}


void 
stream_clicked_cb  (GtkButton   *button, TestGtkBrowser *browser)
{
  const char *data;
  const char *data2;
  data = "<html>Hi";
  data2 = " there</html>\n";
  g_print("stream_clicked_cb\n");
  gtk_moz_embed_open_stream(GTK_MOZ_EMBED(browser->mozEmbed),
			    "file://", "text/html");
  gtk_moz_embed_append_data(GTK_MOZ_EMBED(browser->mozEmbed),
			    data, strlen(data));
  gtk_moz_embed_append_data(GTK_MOZ_EMBED(browser->mozEmbed),
			    data2, strlen(data2));
  gtk_moz_embed_close_stream(GTK_MOZ_EMBED(browser->mozEmbed));
}


gboolean
delete_cb(GtkWidget *widget, GdkEventAny *event, TestGtkBrowser *tbrowser)
{
  sio_write(SIO_DEBUG, "Window closed, main=%d", (tbrowser==browser));
  gtk_widget_destroy(widget);
  if (tbrowser == browser) {
	gtk_main_quit();
  };
  return TRUE;
}

void
destroy_cb   (GtkWidget *widget, TestGtkBrowser *browser)
{
  sio_write(SIO_DEBUG, "destroy_cb");
  gtk_main_quit();
}

void
location_changed_cb (GtkMozEmbed *embed, TestGtkBrowser *browser)
{
  char *newLocation;
  newLocation = gtk_moz_embed_get_location(embed);
  sio_setvar("real_location", "+:s", newLocation ? newLocation : "");
  if (browser->url) free(browser->url);
  browser->url = strdup(newLocation);
  if (newLocation)
    g_free(newLocation);
}

void
title_changed_cb    (GtkMozEmbed *embed, TestGtkBrowser *browser)
{
  char *newTitle;
  newTitle = gtk_moz_embed_get_title(embed);
  sio_setvar("title", "+:s", newTitle ? newTitle : "");
  if (newTitle)
  {
    g_free(newTitle);
  }
}

void
load_started_cb     (GtkMozEmbed *embed, TestGtkBrowser *browser)
{
  sio_setvar("loading", "+:d", 1);
}

void
load_finished_cb    (GtkMozEmbed *embed, TestGtkBrowser *browser)
{
  sio_setvar("progress", "+:ss", "", "");
  sio_setvar("loading", "+:d", 0);
}


void
net_state_change_cb (GtkMozEmbed *embed, gint flags, guint status,
		     TestGtkBrowser *browser)
{
  //net_state_change_all_cb(embed, browser->url, flags, status, browser);  
}

void net_state_change_all_cb (GtkMozEmbed *embed, const char *uri,
				     gint flags, guint status,
				     TestGtkBrowser *browser)
{
  //  g_print("net_state_change_all_cb %s %d %d\n", uri, flags, status);
  //sio_write(SIO_DEBUG, "net-state-change-all\t%s\t%d\t%d", uri, flags, status);
  std::string stat;
  if (flags & GTK_MOZ_EMBED_FLAG_IS_REQUEST) {
    if (flags & GTK_MOZ_EMBED_FLAG_REDIRECTING)
    stat = "Redirecting to site...";
    else if (flags & GTK_MOZ_EMBED_FLAG_TRANSFERRING)
    stat = "Transferring data from site...";
    else if (flags & GTK_MOZ_EMBED_FLAG_NEGOTIATING)
    stat = "Waiting for authorization...";
  }

  if (status == GTK_MOZ_EMBED_STATUS_FAILED_DNS)
    stat += "Site not found.";
  else if (status == GTK_MOZ_EMBED_STATUS_FAILED_CONNECT)
    stat += "Failed to connect to site.";
  else if (status == GTK_MOZ_EMBED_STATUS_FAILED_TIMEOUT)
    stat += "Failed due to connection timeout.";
  else if (status == GTK_MOZ_EMBED_STATUS_FAILED_USERCANCELED)
    stat += "User canceled connecting to site.";

  if (flags & GTK_MOZ_EMBED_FLAG_IS_DOCUMENT) {
    if (flags & GTK_MOZ_EMBED_FLAG_START)
      stat += "Loading site...";
    else if (flags & GTK_MOZ_EMBED_FLAG_STOP)
      stat += "Done.";
  }

  sio_write(SIO_DEBUG|30, "Status change\t%X\t%s\t%x\t%x\t%s", 
			embed, stat.c_str(), flags, status, uri?uri:"{null}");
}

void progress_change_cb   (GtkMozEmbed *embed, gint cur, gint max,
			   TestGtkBrowser *browser)
{
  sio_setvar("progress", "+:dd", cur, max);
}

void progress_change_all_cb (GtkMozEmbed *embed, const char *uri,
			     gint cur, gint max,
			     TestGtkBrowser *browser)
{
  //sio_write(SIO_DEBUG, "progress_change_all_cb %s cur %d max %d", uri, cur, max);
}

void
link_message_cb      (GtkMozEmbed *embed, TestGtkBrowser *browser)
{
  char *message;
  message = gtk_moz_embed_get_link_message(embed);
  sio_setvar("temp_message", "+:ss", message?message:"", (message&&*message)?"link":"");
  if (message)
    g_free(message);
}

void
js_status_cb (GtkMozEmbed *embed, TestGtkBrowser *browser)
{
  char *message;
  message = gtk_moz_embed_get_js_status(embed);  
  sio_setvar("temp_message", "+:ss", message?message:"", (message&&*message)?"js":"");
  if (message)
    g_free(message);
}

void
new_window_cb (GtkMozEmbed *embed, GtkMozEmbed **newEmbed, guint chromemask, TestGtkBrowser *browser)
{
  sio_write(SIO_DEBUG, "new window request(cmask=%X)", chromemask);
  //TestGtkBrowser *newBrowser = new_gtk_browser(chromemask);	
  //gtk_widget_set_usize(newBrowser->mozEmbed, 400, 400);	
  //*newEmbed = GTK_MOZ_EMBED(newBrowser->mozEmbed);
  //g_print("new browser is %p\n", (void *)*newEmbed);
  *newEmbed = 0;
}

void
visibility_cb (GtkMozEmbed *embed, gboolean visibility, TestGtkBrowser *browser)
{
  sio_setvar("visibility", "+:d", visibility);
  set_browser_visibility(browser, visibility);
}

void
destroy_brsr_cb      (GtkMozEmbed *embed, TestGtkBrowser *browser)
{
  //sio_write(SIO_DEBUG, "destroy_brsr_cb");
  sio_write(SIO_LOG, "Browser called window.close() - ignoring");
  //gtk_widget_destroy(browser->topLevelWindow);
}

gint
open_uri_cb          (GtkMozEmbed *embed, const char *uri, TestGtkBrowser *browser)
{
  if ((!strcmp(uri, browser->url)) || (!strcmp(req_loc, uri))) {	
	sio_write(SIO_DEBUG, "Opening main URL\t%s", uri);
  } else {
	sio_write(SIO_DEBUG, "Opening frame URL\t%s", uri);
  };
  // real location is always OK to load...
  if (!strcmp(req_loc, uri))
	return FALSE;

  // TODO: check the kiosk ruleset...
  //if (!url_accepted(uri))  return TRUE;

  // don't interrupt anything else
  return FALSE;
}

void
size_to_cb (GtkMozEmbed *embed, gint width, gint height,
	    TestGtkBrowser *browser)
{
  sio_write(SIO_LOG, "size_to_cb %d %d - rejected", width, height);
  //gtk_widget_set_usize(browser->mozEmbed, width, height);
}

gint dom_key_down_cb      (GtkMozEmbed *embed, nsIDOMKeyEvent *event,
			   TestGtkBrowser *browser)
{
  PRUint32 keyCode = 0;
  //  g_print("dom_key_down_cb\n");
  event->GetKeyCode(&keyCode);
  sio_write(SIO_DEBUG, "key down, key code is %d", keyCode);
  return NS_OK;
}

gint dom_key_press_cb     (GtkMozEmbed *embed, nsIDOMKeyEvent *event,
			   TestGtkBrowser *browser)
{
  PRUint32 keyCode = 0;
  // g_print("dom_key_press_cb\n");
  event->GetCharCode(&keyCode);
  sio_write(SIO_DEBUG, "key press, key code is %d", keyCode);
  // g_print("char code is %d\n", keyCode);
  return NS_OK;
}

gint dom_key_up_cb        (GtkMozEmbed *embed, nsIDOMKeyEvent *event,
			   TestGtkBrowser *browser)
{
  PRUint32 keyCode = 0;
  // g_print("dom_key_up_cb\n");
  event->GetKeyCode(&keyCode);
  sio_write(SIO_DEBUG, "key up, key code is %d", keyCode);
  // g_print("key code is %d\n", keyCode);
  return NS_OK;
}


int handle_mouse(int type, GtkMozEmbed *embed, nsIDOMMouseEvent *event, TestGtkBrowser *browser) {
  PRInt32 x=-1, y=-1;
  PRUint16 btn=1000;
  event->GetClientX(&x);
  event->GetClientY(&y);
  event->GetButton(&btn);
  sio_write(SIO_DEBUG, "mouse event\t%d\t%d\t%d\t%d", 
			type, x, y, btn);  
  return NS_OK;
};

gint dom_mouse_down_cb    (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
			   TestGtkBrowser *browser)
{
  //  g_print("dom_mouse_down_cb\n");
  return handle_mouse(1, embed, event, browser);
}

gint dom_mouse_up_cb      (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
			   TestGtkBrowser *browser)
{
  return handle_mouse(2, embed, event, browser);
}

gint dom_mouse_click_cb   (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
			   TestGtkBrowser *browser)
{
  return handle_mouse(3, embed, event, browser);
}

gint dom_mouse_dbl_click_cb (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
			     TestGtkBrowser *browser)
{
  return handle_mouse(4, embed, event, browser);
}

gint dom_mouse_over_cb    (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
			   TestGtkBrowser *browser)
{
  return NS_OK; //handle_mouse(5, embed, event, browser);

}

gint dom_mouse_out_cb     (GtkMozEmbed *embed, nsIDOMMouseEvent *event,
			   TestGtkBrowser *browser)
{
  return NS_OK; //handle_mouse(6, embed, event, browser);
}

gint dom_activate_cb      (GtkMozEmbed *embed, nsIDOMUIEvent *event,
			   TestGtkBrowser *browser)
{
  //g_print("dom_activate_cb\n");
  return NS_OK;
}

gint dom_focus_in_cb      (GtkMozEmbed *embed, nsIDOMUIEvent *event,
			   TestGtkBrowser *browser)
{
  //g_print("dom_focus_in_cb\n");
  return NS_OK;
}

gint dom_focus_out_cb     (GtkMozEmbed *embed, nsIDOMUIEvent *event,
			   TestGtkBrowser *browser)
{
  //g_print("dom_focus_out_cb\n");
  return NS_OK;
}

void new_window_orphan_cb (GtkMozEmbedSingle *embed,
			   GtkMozEmbed **retval, guint chromemask,
			   gpointer data)
{
  sio_write(SIO_DEBUG, "New Window Orphan (mask=%X)", chromemask);
  //TestGtkBrowser *newBrowser = new_gtk_browser(chromemask);
  //*retval = GTK_MOZ_EMBED(newBrowser->mozEmbed);
  //g_print("new browser is %p\n", (void *)*retval);
  *retval = 0;
}


