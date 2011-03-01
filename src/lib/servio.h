#ifndef _SERVIO_H_
#define _SERVIO_H_

#include <string>

// communication with server

// open comms. 0 for ok, -1 for error
// parses command-line arguments, removes parsed, adds the ones that came from config file
// uses SODACTRL_PORT and SODACTRL_IP env variables
// NOTE: if SODACTRL_PORT is unset, uses STDIN/STDOUT for server comm
// if SERVIO_DEBUG is set, this is debug level (def 50; LOG=+100, WARN=+400, ERR=+500)
// SERVIO_COMMDUMP is bitflag: 1=show writes, 2=show reads, 
// if 
// NOTE: if -1 is returned, program should exit ASAP
// NOTE: the connection is open in the 'exclusive' mode (only one app with given appname allowed)
//       if you do not want this, put '+' in front of the appname
int sio_open(int &argc, char ** &argv, const char* appname, const char* ver, const char * client=0);


// message priorities
#define SIO_DEBUG    0x1000
#define SIO_DATA     0x2000
#define SIO_LOG      0x3000
#define SIO_WARN     0x4000
#define SIO_ERROR    0x5000

// write to comm channel
//  message CAN contain up to 3 args
//  message CAN NOT conatin a newline
//   0 for ok, -1 for error
// "level" is one of SIO_ constants above, possibly OR'ed with 
//   debug level required (1..100, 1 = most verbose, 100=least verbose)
int sio_write(int level, const char * format, ...);



#define SR_TIMEOUT		0
#define SR_ERROR		-1
#define SR_USERFD		-3

// read from comm channel  (or from 'postponed' buffer if tis is not empty)
// waits up to X milliseconds, 0 for poll, -1 for blocking
// RV:   
//       >0           = data returned, RV is data length
//       SIO_TIMEOUT  = 0  = timeout - no data ever came
//       SIO_ERROR    = -1 = error, terminate the program
//       SIO_USERFD   = -3 = pollfd got selected
// if "pollfd" is not -1, then it will be select()'ed on; the timeout will be terminated
//    if it selected for read
// NOTE: if -1 is returned, program should exit ASAP
// NOTE: result might be changed even in case of timeout or error.
// NOTE: if two threads both call read(), the second read will fail with sr_error
int sio_read(std::string &result, int timeout=-1, int pollfd = -1);

// read the expected mesage from channel
// read messages until something that matches given prefixes comes up (see sio_matchpref)
// messages that do not match get placed into 'postponed' buffer and would be returned by next sio_read() call
// RV:
//     >0               = prefix with that index matched (1-based)
//     SIO_TIMEOUT =  0 = timed out
//     SIO_ERROR   = -1 = error occured, terminate the program
// NOTE: result might be changed even in case of timeout or error.
int sio_readexpect(std::string &result, const char * prefix, int * preflen = 0, int timeout=-1);

// C version of the above (for compatibility only)
//   data is also guaranteed to be null-terminated and not to contain any EOL characters
// it writes up to (maxbuff-2) bytes, so double-null termination is possible
int sio_read(char * buff, int buffsize, int timeout=-1, int pollfd=-1);

typedef struct sio_mmatch {
  std::string message; /// whole message
  int pnum;   // number of prefix that matched (1-based)
  int plen;   // length of matching prefix
} sio_mmatch;

//  match function
//  args:
//     minfo    - match info - pointer to sio_mmatch structure
//     userarg  - user-specified value
//  RV:
//     0 to 'eat' the message (sio_read continues until timeout)
//     1 to return the message to user program
//    -1 to make sio_read fail
typedef int (*siomessage_func)(sio_mmatch * minfo, void * userarg);

// install match function
// function is called on any message which matches the given prefixes, just before sio_read returns
//  it has opportunity to make message disapper (the sio_read continues, the processing time is substarted from time remaining)
//  or to return it to the user.
// do not eat generic SYS-VALUE message - this might make sio_getvar timeout.
// args: 
//    prefix  - prefixes to match (see sio_matchpref)
//    func    - function pointer (see siomessage_func)
//    uarg    - user argument to match function
// RV:
//    >0 for OK
int sio_setmatchfunc(const char * prefix, siomessage_func * func, void * userarg);

// helper: parse given buffer. the buffer is garbled.
// argv[i] points to given token
// all unused cells are set to 0
// argv_size is sizeof(argv)
// return value is argc
int sio_parse(char*buff, char ** argv, int argv_size);

// helper: match any prefix. The prefixes must be delimited by \n
// if there is no match, returns 0; otherwise, 1+number of prefix matched
// if plen is not null, it will get the length of matching prefix
int sio_matchpref(const char * message, const char * prefixes, int*plen = 0);

// helper: returns Nth field in the string; 0 is command name; retruns empty string if index too big
std::string sio_field(const std::string & msg, int field);

// high-level function: get variable
//   varname is the variable name (so far, only scalars are supported)
//   application name is the one used in registration, unless overriden with "a" 
//   format is used to parse resulting list of values. It can be:
//      d   - value is an integer (in decimal representation), will be stored to int* provided
//      f   - value is floating point (in decimal representation), will be stored to double* provided
//      s   - value is a string, pointer will be allocated by library and will be stored to char** provided
//            NOTE: this variable must be initialized to free()'able value - it would be free on update
//      S   - value is a string, will be stored to std::string* provided (which must be intialized)
//      R   - store the rest of values (with tabls) to std::string* pointer provided (which must be intialized)
//   format can also contain the following flags which apply to all arguments
//      a   - next arg is const char* with application name
//      A   - next arg is std::string* with application name
//      k   - next arg is a const char* to the key name for the maps
//      K   - next arg is a std::string* with key name
//      i   - next arg is int which is converted to string representation and used as a key name
//      t   - next arg is an int which sets the timeout 
//      C   - next arg is pointer to siomessage_func which will be called if variable is changed
//      P   - next arg is pointer which will be passed as arg to siomessage_func
//      +   - remember the parameters, put a watch on SYS-SET with correct args, and update the variable in memory anytime someone chages it on server.
//      ?   - do not wait for server response; the value would be set during next sio_read call. Implies +
//      w   - a warning will be made to server log if value is empty
//      D   - if variable is not set, the current value would be set as default
// NOTE: flags must be be before the arguments, and separated by ':'
//  example: to get integer value CTOOL.test to itest:
//     sio_getvar("test", "a:d", "CTOOL", &itest);
// RV:
//      1   if variable value was recieved
//      0   if timeout occured or ? was specified
//     -1   if error of some sort ocured
// WARNING: not thread-safe!!
int sio_getvar(const char * varname, const char* format, ...);


// high-level function: set variable
//   varname is variable name
//   format is used to parse input list. It can be:
//      d   - next arg is taken as int and converted to string
//      s   - next arg is const char*
//      S   - next arg is const std::string* 
//      R   - next arg is const std::string*, but the tabs are not removed and binary encoding is not done
//   format can also contain the flags which apply to all arguments. The values are the same as in sio_getvar, except:
//      +   - remember that parameters' values; if sio_setvar will be called with the same name and value, no 
//            messages would be sent
//      ?   - do not use
//      w, C, P - ignored
// RV: 
//      1   if variable was sent
//      0   if + was specified and variable did not change 
//     -1   if error occured
// WARNING: not thread-safe!!
int sio_setvar(const char *varname, const char* format, ...);

// call before exit - flushes all buffers
void sio_close(int excode=0, char*comment="");

// helper - useconds since epoch as 64-bit int
#ifndef int64
typedef long long int int64;
#endif
int64 time64();

// multithreading:
//  install 'global lock' / 'global unlock' handlers
//  they would be called at start and end of each function
//  if global_lock returns -1, whole function will also return -1
// call this AFTER sio_open, but before any other function
int sio_register_lock( int (*glob_lock)(void * arg),
		       int (*glob_unlock)(void * arg),
		       void * arg );


#if !defined(min)
#define min(x, y)   (( (x) < (y) ) ? (x) : (y))
#endif

#endif
