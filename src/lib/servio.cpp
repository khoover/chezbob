#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/select.h>
#include <sys/time.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdarg.h>
#include <stdlib.h>

#include <string>
#include <deque>
#include <map>
#include <list>
#include <vector>

#include "servio.h"

static int ser_fd_read = -1;
static int ser_fd_write = -1;

static std::string readbuf;

int sio_dbglevel;

static int eol_char = '\n';

int sio_commdump = 0;

static const char * appname = "??";

static std::deque<std::string> postponed;

class SIOMessageHandler {
public:
  char * prefix;
  siomessage_func func;
  void * userarg;

};

static int noserv_mode;

static std::list<SIOMessageHandler*> matchlist;


static int (*sio_glob_lock_f)(void * arg) = 0;
static int (*sio_glob_unlock_f)(void * arg) = 0;
static void * sio_lock_arg = 0;

#define GLOB_LOCK()    { if (sio_glob_lock_f) { if (sio_glob_lock_f(sio_lock_arg)<0) return -1; }; }
#define GLOB_UNLOCK()  { if (sio_glob_unlock_f) { sio_glob_unlock_f(sio_lock_arg); };  }

class SIOVarRecord {
public:
  // parse declaration
  // 1 = parse went ok; advances both pointers
  int parse_decl(const char * varname, const char * format, va_list& args, bool get_decl);

  // parse message, set values
  int parse_value_set(std::string msg, int preflen=0);

  // parse pointers, generate values suitable for SYS-SET
  std::string get_current_vals();

  int warn;
  int remember; // 0 - no, 1 - remeber, 2 - remeber + nocache
  int timeout;
  int setdefault;

  std::string fullname; // app<tab>addr<tab>key
  std::string app;
  std::string name;
  std::string key;

  std::vector<char> types;
  std::vector<void*> valptr;
  std::vector<std::string> values;

  siomessage_func ufunc;
  void * uarg;
};

static std::map<std::string,SIOVarRecord*> varlist;

int write_full(int fd, void * buff, int size) {
  int r, left;
  left = size;
  while (left > 0) {
	r = write(fd, (char*)buff, left);
	if (r==0) { errno = 0; return -1; };
	if (r<=0) return -1;
	(*((char**)&buff))+=r;
	left-=r;
  };
  return size;
};


int sio_open(int &argc, char ** &argv, const char*g_appname, const char*ver, const char*client) {
  
  char * port_str = getenv("SODACTRL_PORT");
  if (port_str) {
	// connect socket
	int port = atoi(port_str);
	if (port <= 0) {
	  fprintf(stderr, "Invalid port number (SODACTRL_PORT): %s\n", port_str);
	  return -1;
	};
	int fd = socket(AF_INET, SOCK_STREAM, 0);
	if (fd < 0) {
	  perror("Cannot create socket"); return -1;
	};
	struct linger ling;
	ling.l_onoff = 1;
	ling.l_linger = 10; // try to send data for up to 10 seconds...
	if (setsockopt(fd, SOL_SOCKET, SO_LINGER, &ling, sizeof(ling)) < 0) {
	  perror("setsockopt(linger) failed");
	};

	struct sockaddr_in servaddr;
	struct hostent *host;
	bzero(&servaddr, sizeof(servaddr));
	servaddr.sin_family = AF_INET;
	servaddr.sin_port = htons(port);
	const char * ip =  getenv("SODACTRL_IP");
	if (!ip) ip = "127.0.0.1";
	servaddr.sin_addr.s_addr =inet_addr(ip);

	if (connect(fd, (sockaddr*)&servaddr, sizeof(servaddr)) < 0){
	  char bf[512];
	  snprintf(bf, sizeof(bf), "Cannot connect to %s:%d", ip, port);
	  perror(bf);
	  return -1;
	}
	ser_fd_read = ser_fd_write = fd;

  } else {
	// use STDIN/STDOUT
	ser_fd_read = 0;
	ser_fd_write = 1;
  };

  fcntl(ser_fd_read, F_SETFL, O_NONBLOCK);
  fcntl(ser_fd_write, F_SETFL, O_NONBLOCK);
  
  char * dbgc = getenv("SERVIO_DEBUG");
  sio_dbglevel = dbgc ? atoi(dbgc) : 50;

  char * commd = getenv("SERVIO_COMMDUMP");
  sio_commdump = commd ? atoi(commd) : 0;

  const char* proto = "106";

  if (g_appname[0] == '+') {
	proto = "101";
	g_appname++;
  };

  appname = strdup(g_appname);
  if (sio_write(SIO_DATA, "SYS-INIT\t%s\t%s\t%s\t%d\t%s",
				proto, appname, ver, getpid(), (client?client:"")) == -1) {
	perror("Cannot write to server");
	return -1;
  };

  
  noserv_mode = 0; 
  // no need for 'SYS_WELCOME' when debug env is set - thus can run from console easliy
  if (isatty(ser_fd_read) && (ser_fd_read != ser_fd_write)) {
	noserv_mode = 1;
	printf("Using NO-SERVER mode - taking data, commands from tty, disabling GET\n");
	return 0;
  };

  // the only possible response to SYS-INIT with version 101 is SYS-WELCOME
  // wait 10 seconds for it...
  std::string resp;
  if (sio_read(resp, 10*1000) <= 0)  { 
	fprintf(stderr, "Server initial response timed out\n");
	return -1; // no reponse
  };
  if (resp.substr(0, 12)!="SYS-WELCOME\t") {
	for (int i=0; i<resp.length(); i++) 
	  if (resp[i]<32) resp[i]='#';
	fprintf(stderr, "Server initial response is junk: %s\n", resp.c_str());
	return -1;
  };
  return 0;
};


int sio_write(int level, const char * format, ...) {
  char bf[1024];

  int ilevel = level & 0xFFF;
  if (ilevel==0) ilevel = 50;  

  switch (level & 0xF000) {
  case SIO_DATA:    ilevel = sio_dbglevel+1; bf[0] = 0; break;
  case SIO_DEBUG:   sprintf(bf, "SYS-DEBUG\t%s\t%d\t", appname, ilevel); break;
  case SIO_LOG:     ilevel += 100; sprintf(bf, "SYS-LOG\t%s\t", appname); break;
  case SIO_ERROR:   ilevel += 500; sprintf(bf, "SYS-LOG\t%s\tERR: ", appname); break;
  case SIO_WARN:    ilevel += 400; sprintf(bf, "SYS-LOG\t%s\tWARN: ", appname); break;
  default:
	sprintf(bf, "SYS-LOG\tag%X: ", level);
  };

  if (ilevel < sio_dbglevel) return 0;


  va_list args;
  va_start(args, format);
  vsnprintf(strchr(bf,0), sizeof(bf)-strlen(bf)-4, format, args);
  va_end(args);
  strcat(bf, "\n");

  if (sio_commdump & 1) {
	printf("WRITE\t%s", bf);
  };

  GLOB_LOCK();
  write_full(ser_fd_write, bf, strlen(bf));
  GLOB_UNLOCK();
  return 0;
};


int max(int i1, int i2) {
  return (i1>i2)?i1: i2;
};

int sio_read(char * buff, int maxbuff, int timeout, int pollfd) {
  std::string data;
  int rv= sio_read(data, timeout, pollfd);
  if (rv > 0) {
	if (rv > (maxbuff-4)) rv = maxbuff-4;
	memcpy(buff, data.data(), rv);
	buff[rv]=0;	
  } else {
	buff[0] = 0;
  };
  return rv;
};


// internal: handle message
//  return 1 to return to user, 0 to eat, othere to return this error
int _sio_handlemsg(std::string & msg) {
  
  // system handler
  if (msg.substr(0, 10)=="SYS-CPING\t") {
	std::string r2 =  msg.substr(10);
	if (sio_write(SIO_DATA, "SYS-CPONG\t%s", r2.c_str())==-1) {
	  return -1;
	};
	return 0;
  };


  int rv = 1; // return to user

  // message match handler
  int plen = 0;
  if (sio_matchpref(msg.c_str(), "SYS-SET\t", &plen)>0) {
	int evar = msg.find('\t', plen) + 1; // skip appname
	evar = msg.find('\t', evar) + 1; // skip varname
	evar = msg.find('\t', evar) + 1; // skip key
	if (evar<plen) evar=plen;
	std::string pref = msg.substr(plen, evar-plen-1);

	int mcount = 0;
	for (std::map<std::string,SIOVarRecord*>::iterator i=varlist.find(pref); i!=varlist.end(); i++) {
	  //printf("key = [%s], val=[0x%X]\n", i->first.c_str(), i->second);
	  if (i->first == pref) {
		SIOVarRecord * r = i->second;
		if (r) {
		  rv = r->parse_value_set(msg, evar);
		  mcount++;
		};
		//mcount += 100;
	  };
	  //mcount+=1000;
	};
	
	//printf("got sys-get to [%s] from [%s], matched %d\n", pref.c_str(), msg.c_str(), mcount);
  };

  sio_mmatch m;


  // other stuff
  for (std::list<SIOMessageHandler*>::iterator ll=matchlist.begin(); ll != matchlist.end(); ll++) {
	m.pnum = sio_matchpref(msg.c_str(), (*ll)->prefix, &m.plen);
	if (m.pnum > 0) {
	  m.message = msg;
	  int r = ((*ll)->func)(&m, (*ll)->userarg);
	  if (r < rv) rv = r; 
	};
  };

  return rv;
};


int sio_setmatchfunc(const char * prefix, siomessage_func func, void * userarg) {

  SIOMessageHandler * msh = new SIOMessageHandler();
  msh->prefix = strdup(prefix);
  msh->func = func;
  msh->userarg = userarg;

  matchlist.push_back(msh);

  return 1;
};

static int inside_read = 0;

int sio_read(std::string &result, int timeout, int pollfd) {
  int once = 1;
  GLOB_LOCK();

  if (!postponed.empty()) {
	result = postponed.front();
	postponed.pop_front();
	//printf("accepted: [%s] (%d)\n", result.c_str(), postponed.size());
	GLOB_UNLOCK();
	return result.length();
  };

  if (inside_read) {    
    GLOB_UNLOCK();
    sio_write(SIO_ERROR, "recursive sio_read");
    return -1;
  };

  int64 stoptime = time64() + timeout*1000;

  while (once || (stoptime > time64())) {
	once = 0;
	int eol_pos = readbuf.find(eol_char);
	if (eol_pos != std::string::npos) {
	  result = readbuf.substr(0, eol_pos);
	  readbuf = readbuf.substr(eol_pos+1);

	  if (sio_commdump & 2) {
		printf("READ\t%s\n", result.c_str());
	  };

	  GLOB_UNLOCK();

	  int rv = _sio_handlemsg(result); // might call other functs
	  if (rv == 0) {
	    GLOB_LOCK();
	    continue;
	  };
	  if (rv < 0) return rv;
	  return result.length();
	};
  
	inside_read = 1;
	GLOB_UNLOCK();

	// wait for some more data...
	fd_set fdr; struct timeval tv;
	int delta = (int)( (stoptime - time64()) / 1000 );
	if (delta < 0) delta = 0;
	tv.tv_sec = delta/1000;  tv.tv_usec = (delta%1000)*1000;
	FD_ZERO(&fdr); FD_SET(ser_fd_read, &fdr);
	if (pollfd!=-1) FD_SET(pollfd, &fdr);
	int rv = select(max(ser_fd_read, pollfd)+1, &fdr, 0, 0, (timeout>=0)?&tv:0);
	if ( (rv<0) && (errno != EINTR) ) {
	  inside_read = 0;
	  return -1; // error
	};

	if (pollfd != -1) if (FD_ISSET(pollfd, &fdr)) {
	  inside_read = 0;
	  return -3; // pollfd is select'ed
	};

	GLOB_LOCK();
	inside_read = 0;
	char bf[257];
	rv = read(ser_fd_read, bf, sizeof(bf)-1);
	if ( (rv<=0) && (errno!=EINTR) && (errno != EAGAIN)) {
	  GLOB_UNLOCK();
	  return -1; // error or timeout
	};
	if (rv<0) continue;
	if (rv==0) {
	  GLOB_UNLOCK();
	  return -1; // EOF from server
	};
	bf[rv]=0;
	//printf("\n\nREAD[[[%s]]]\n", bf);
	readbuf = readbuf + bf;
  };

  GLOB_UNLOCK();
  return 0; // timeout
};


// MT safe
int sio_readexpect(std::string &msg, const char * prefix, int * preflen, int timeout) {

  std::deque<std::string> rejected;

  // true timeout
  int64 stoptime = time64() + timeout*1000;

  int rv;
  while (stoptime > time64()) {
	int delta = (int)( (stoptime - time64()) / 1000 );
	rv=sio_read(msg, (delta>0)?delta:0);
	if (rv <= 0) break; //  error or timeout
	rv = sio_matchpref(msg.c_str(), prefix, preflen);
	if (rv > 0) break; // found it
	rejected.push_back(msg); 
	//printf("rejected: [%s] (%d)\n", msg.c_str(), rejected.size());
  };

  // push back the unanswered messages...
  std::string tmp;
  while (!rejected.empty()) {
	tmp = rejected.back();
	rejected.pop_back();
	postponed.push_front(tmp);
	//printf("postponed: [%s] (%d)\n", tmp.c_str(), postponed.size());
  };

  //printf("MESSAGE [%s] is number %d in list of\n%s\n", msg.c_str(), rv, prefix);
  return rv;
};


int sio_parse(char*buff, char ** argv, int argv_size) {
  bzero(argv, argv_size);
  int icount = 0;
  char * pos = buff;
  argv[0] = pos; icount++;
  while (argv_size>(icount*sizeof(char*))) {
	while ((*pos!=0) && (*pos!='\t')) pos++;
	if (*pos==0) break; // end of string
	*pos=0;	pos++;
	argv[icount]=pos; icount++;
  };
  return icount;
};


// as $ sign in front of the match will make last charater match EOL too
int sio_matchpref(const char * message, const char * prefixes, int *plen) {
  int numpref = 0;
  const char * start = prefixes;
  while (*start) {
	const char * end = start;
	while (*end && (*end != '\n')) end++;
	int match_eol = (start[0] == '$');
	if (match_eol) start++;
	numpref++;
	if (strncmp(message, start, end-start)==0) {
	  if (plen) *plen = end-start;
	  return numpref;
	} else if (match_eol && 
			   (strncmp(message, start, end-start-1)==0) && 
			   (message[end-start-1]==0)) {
	  if (plen) *plen = end-start-1;
	  return numpref;
	};
	start = end+(*end?1:0);
  };
  return 0;
};

std::string sio_field(const std::string & msg, int field) {
  int i = 0;
  while ((field > 0) && (i>=0)) {
	i = msg.find('\t', i);
	if (i>=0) i++;
	field--;
  };
  if (i < 0) return "";
  int j = msg.find('\t', i+1);
  if (j < 0) return msg.substr(i);
  else return msg.substr(i, j-i);
};

//static map<std::string,SIOVarRecord*> varlist;

int SIOVarRecord::parse_decl(const char * varname, const char * format, va_list& args, bool get_decl) {
  warn = 0;
  remember = 0;
  app = appname;
  name = std::string(varname);
  key = "";
  timeout = 1000;
  ufunc = 0;
  uarg = 0;
  setdefault = 0;
  types.clear();
  valptr.clear();
  values.clear();


  char bfi[64];
  const char * fmptr = format;

  // parse flags
  if (strchr(fmptr, ':')) {
	while (*fmptr != ':') {
	  switch (*fmptr) {
	  case 'w': warn = 1; break;
	  case 'a': app =  std::string(va_arg(args, char*)); break;
	  case 'A': app =            *(va_arg(args, std::string*)); break;
	  case 'k': key =  std::string(va_arg(args, char*)); break;
	  case 'K': key =            *(va_arg(args, std::string*)); break;
	  case 'i': sprintf(bfi, "%d", va_arg(args, int)); key = std::string(bfi); break;
	  case 't': timeout =          va_arg(args, int); break;
	  case 'C': ufunc =            va_arg(args, siomessage_func); break;
	  case 'P': uarg =             va_arg(args, void*); break;
	  case 'D': setdefault = 1;
	  case '+': if (remember < 1) remember = 1; break;
	  case '?': if (remember < 2) remember = 2; break;
	  default: // this includes 0 for end-of-string
		sio_write(SIO_ERROR, "invalid flags to sio_*var: %s", format);
		return -1; // failed
	  };	
	  fmptr++;
	};
	fmptr++;  // skip the :
  };

  int fcount = 0;
  while (*fmptr) {
	char type = *fmptr;
	if (!strchr("dfsSR", type)) {
	  sio_write(SIO_ERROR, "invalid format #%d to sio_getvar: %s", fcount+1, format);
	  return -1; // failed
	};
	types.push_back(type);

	// for both, push current values
	std::string t;

	if (get_decl) {
	  // varget - push pointers	
	  void* ptr = va_arg(args, void*);
	  valptr.push_back(ptr);

	  switch (type) {
	  case 'd': sprintf(bfi, "%d", *((int*)ptr)); t = bfi; break;
	  case 'f': sprintf(bfi, "%g", *((double*)ptr)); t = bfi;  break;
	  case 's': t = (*(char**)ptr) ? (*(char**)ptr) : ""; break;
	  case 'S': t = *((std::string*)ptr); break; //TODO: tabremove
	  case 'R': t = *((std::string*)ptr); break;
	  };	

	} else {
	  // varset - no pointers to push
	  
	  valptr.push_back(0);
	  switch (type) {
	  case 'd': sprintf(bfi, "%d", va_arg(args, int)); t = bfi; break;
	  case 'f': sprintf(bfi, "%g", va_arg(args, double)); t = bfi;  break;
	  case 's': t = va_arg(args, char*); break;
	  case 'S': t = *(va_arg(args, std::string*)); break; //TODO: tabremove
	  case 'R': t = *(va_arg(args, std::string*)); break;
	  };	

	};
	values.push_back(t);

	//if (type == 's') {	  *((char**)values[fcount]) = 0;};
	fcount++;
	fmptr++;
  };

  fullname = app + "\t" + name + "\t" + key;

  return 1;
};


int SIOVarRecord::parse_value_set(std::string msg, int preflen) {
  const char * start;
  if (preflen == -1) {
	const char * pp = msg.c_str();
	start = strchr(pp, '\t'); //skip event
	if (start) start = strchr(start+1, '\t'); // skip appname
	if (start) start = strchr(start+1, '\t'); // skip varname
	if (start) start = strchr(start+1, '\t'); // skip index
	if (!start) start = pp; // this should never happen, but...
	else if (*start) start++;
	preflen = start - pp;
  } else {
	start = msg.c_str() + preflen;
  };
  
  bool empty = false;
  for (int i=0; i<types.size(); i++) {
	if (warn && !*start) {
	  sio_write(SIO_WARN, "variable %s.%s[%s].%d has no value for type %c", app.c_str(), name.c_str(), key.c_str(), i, types[i]);
	};  
	const char * end = strchr(start, '\t');
	const char * next;
	if (end==0) { 
	  end = strchr(start, 0); 
	  next = end; 
	} else {
	  next = end + 1; 
	};
	if (0) {
	  //*end=0; 
	  sio_write(SIO_DEBUG, "variable %s.%s[%s].%d has value %c[%*s]", app.c_str(), name.c_str(), key.c_str(), i, types[i], end-start, start); 
	  //if (next != end) *end='\t';
	};	  
	void* ptr = valptr[i];
	//printf("going to parse p to 0x%X as %c\n", ptr, *fmptr);
	switch (types[i]) {
	case 'd': *((int*)ptr) = atoi(start); break;
	case 'f': *((double*)ptr) = atof(start); break;
	case 's': 
	  if (*((char**)ptr)) free(*(char**)ptr);
	  *((char**)ptr) = strndup(start, end-start); 
	  break;
	case 'S': *((std::string*)ptr) = std::string(start, end-start); break;
	case 'R': *((std::string*)ptr) = std::string(start); 
	  next = strchr(start, 0);  break;
	default: 
	  exit(100);
	  break;
	};	
	start = next;
  };

  int rv = 0; // default eat
  if (ufunc) {
	sio_mmatch m;
	m.message = msg;
	m.pnum = 2;
	m.plen = preflen;
	rv = ufunc(&m, uarg);
  };
  

  return rv;
};



std::string SIOVarRecord::get_current_vals() {

  std::string ret = "";

  for (int i=0; i<types.size(); i++) {
	ret = ret + ( (i?"\t":"") + values[i] ) ;
  };

  return ret;
};

int sio_getvar(const char * varname, const char* format, ...) {

  SIOVarRecord * sivr = new SIOVarRecord();

  va_list args;
  va_start(args, format);
  if (sivr->parse_decl(varname, format, args, true) < 0) {
	delete sivr;
	return -1;
  };
  va_end(args);

  SIOVarRecord * prev = varlist[sivr->fullname];
  if (prev) delete prev;

  int rv = 0;

  // do the query
  sio_write(SIO_DATA, "SYS-GET\t%s", sivr->fullname.c_str());

  std::string expect = "$SYS-VALUE\t" + sivr->fullname + "\t" "\n$SYS-SET\t" + sivr->fullname + "\t";

  if (sivr->remember < 2) {
	std::string msg = "";
	int preflen = 0;
	rv = sio_readexpect(msg, expect.c_str(), &preflen, sivr->timeout);

	if (rv>0) {
	  //printf("data for %s: rv=%d, preflen=%d, msglen=%d\n", varname, rv, preflen, msg.length());
	  if ((msg.length() <= (preflen)) && (sivr->setdefault)) { // no values
		std::string val = sivr->get_current_vals();
		sio_write(SIO_DATA, "SYS-SET\t%s\t%s", sivr->fullname.c_str(), val.c_str());
	  } else {
		rv = sivr->parse_value_set(msg, preflen);
	  };
	};
  };

  if (sivr->warn && (rv<=0)) {
	sio_write(SIO_WARN,  "Could not get var\t%s", sivr->fullname.c_str());
  };

  if (sivr->remember > 0) {
	varlist.erase(sivr->fullname);
	varlist.insert(std::pair<std::string,SIOVarRecord*>(sivr->fullname, sivr));
  } else {
	delete sivr;
  };

  return rv;
};


int sio_setvar(const char * varname, const char* format, ...) {

  SIOVarRecord * sivr = new SIOVarRecord();

  va_list args;
  va_start(args, format);
  if (sivr->parse_decl(varname, format, args, false) < 0) {
	delete sivr;
	return -1;
  };
  va_end(args);

  std::string vals = sivr->get_current_vals();

  if (sivr->remember > 0) {

	SIOVarRecord * prev = varlist[sivr->fullname];
	if (prev) {
	  std::string vals_prev = prev->get_current_vals();
	  if (vals == vals_prev) {
		delete sivr;
		return 0;
	  };
	  delete prev;
	};
	varlist.erase(sivr->fullname); // object was freed in prev. step

	varlist.insert(std::pair<std::string,SIOVarRecord*>(sivr->fullname, sivr));
  };


  // do the query
  int rv = sio_write(SIO_DATA, "SYS-SET\t%s\t%s", sivr->fullname.c_str(), vals.c_str());
  if (rv >= 0) rv = 1;

  if (sivr->remember == 0) {
	delete sivr;
  };

  return rv;
};



void sio_close(int excode, const char*comment) {
  fprintf(stderr, "%s: exiting (%d %s)\n", appname, excode, comment);
  sio_write(SIO_DATA, "SYS-DONE\t%s\t%d\t%s", appname, excode, comment);
  if (ser_fd_write != -1) {	
	close(ser_fd_write);
  };
  if (ser_fd_read  != ser_fd_write)  close(ser_fd_read);
};


int64 time64() {
  struct timeval tv;
  gettimeofday(&tv, 0);
  return (int64)1000000*(int64)tv.tv_sec + (int64)tv.tv_usec;
};

int sio_register_lock( int (*glob_lock)(void * arg),
		       int (*glob_unlock)(void * arg),
		       void * arg ) {
  sio_glob_lock_f = glob_lock;
  sio_glob_unlock_f = glob_unlock;
  sio_lock_arg = arg;
};
