
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <signal.h>

#define VMCSERV_C
#include "sercom.h"
#include "servio.h"
#include "vmcserv.h"

// max statistics frequency, seconds
int stat_max_freq = 40;
// min frequency (used when the only stat is STAT_POLLME)
int stat_min_freq = 3600;
// max time in session (forced reset after that)
int max_sess_time = 400; 


// message inter-byte timeout
#define MSG_TOUT   20
#define MSG_ACK_TOUT   1000


// time of last stat printed
time_t last_stat_time = 0;
// time when session expires, or 0 if not in session
time_t this_sess_expire = 0;

void print_stat() {
  int nz = 0;

  if (last_stat_time){
	stat[STAT_TIME] = time(0) - last_stat_time;
  };

  for (int i=0; i<STATCNT; i++) 	if (stat[i]) nz++;
  int dtime = stat[0];

  char bf[1024];
  strcpy(bf, "VEND-STAT\t");

  for (int i=0; i<STATCNT; i++) {
	stat_total[i] += stat[i];
	if (i!=0) // do TIME last..
	  sio_setvar("stats%", "+k:dd", statnames[i], stat[i], stat_total[i]);
	if (stat[i]) {
	  nz--;
	  if (strlen(bf) > (sizeof(bf)-128)) break;
	  sprintf(strchr(bf,0), "\t%s=%d", statnames[i], stat[i]);
		  //sio_write(SIO_DATA, "VEND-STAT\t%d\t%s\t%d", nz, (int)(statnames[i]), stat[i]);
	  stat[i]=0;
	};
  };

  sio_write(SIO_DATA, bf);

  // do TIME to signify end-of-changes...
  sio_setvar("stats%", "+k:dd", statnames[0], dtime, stat_total[0]);
  last_stat_time = time(0);
};


int stop_num = 0;

void onsignal(int num) { 
  stop_num = num;
};



int main(int argc, char ** argv) {

  char cmd[1024];
  char * cmdv[16];
  int cmdc;
  int cmdlen;
  SER_HANDLE srh;

  char * port = getenv("VMC_CL_PORT");
  if (!port) port="/dev/ttyS0";

  
  if (sio_open(argc, argv, "VMCSERV", VERSION, port) < 0) {
	exit(0);
  };

  sio_write(SIO_DATA, "SYS-ACCEPT\tVEND-");

  srh = ser_open(port, SER_M9N1 | SER_LOWLATENCY | SER_B9600 |
				 SER_SIGTIMEOUTS); 
  if (!srh) {
	sio_close(2, "serial port open failed");
    exit(2);
  };

  signal(SIGHUP, &onsignal); 
  signal(SIGINT, &onsignal);
  signal(SIGTERM, &onsignal);
  signal(SIGPIPE, &onsignal);
  signal(SIGALRM, SIG_IGN); 
  signal(SIGUSR1, SIG_IGN); 
  signal(SIGUSR2, SIG_IGN); 


  int c;
  for (int i=0; i<STATCNT; i++) {
	stat[i]=0;
	stat_total[i] = 0;
  };

  csd_init();

  last_stat_time = time(0);
  stat_total[STAT_TIME] = last_stat_time;
  while (!stop_num) {

	csd_onidle();

	if ((cmdlen=sio_read(cmd,sizeof(cmd), 0))>0) {
	  cmdc = sio_parse(cmd, cmdv, sizeof(cmdv));
	  if (strcmp(cmdv[0], "VEND-RESET")==0) {
		evt_enqueue(EVTCMD_RESET);
	  } else if (strcmp(cmdv[0], "VEND-SSTART")==0) {
		int amoney = (cmdc>1)?atoi(cmdv[1]):0;
		evt_enqueue(EVTCMD_BEGINSESS, amoney);
		this_sess_expire = time(0) + max_sess_time;

	  } else if (strcmp(cmdv[0], "VEND-DENIED")==0) {
		evt_enqueue(EVTCMD_DENIED);
	  } else if (strcmp(cmdv[0], "VEND-APPROVED")==0) {
		int a = (cmdc>1)?atoi(cmdv[1]):0;
		sio_write(SIO_DEBUG, "approved - a=%d", a);
		evt_enqueue(EVTCMD_APPROVED, a);
	  } else if (strcmp(cmdv[0], "VEND-SCANCEL")==0) {
		evt_enqueue(EVTCMD_CANCELSESS);
	  } else if (strcmp(cmdv[0], "VEND-STATUS")==0) {
		evt_enqueue(EVTCMD_STATUS);
	  } else if (strncmp(cmdv[0], "VEND-", 5)==0) {
		sio_write(SIO_DEBUG, "unparseable VEND- command: [%s]:[%s]:[%s]",
				  (int)(cmdv[0]?cmdv[0]:"{null}"),
				  (int)(cmdv[1]?cmdv[1]:"{null}"),
				  (int)(cmdv[2]?cmdv[2]:"{null}"));
	  };
	};

	// error - server shutdown
	if (cmdlen == -1) {
	  break;
	};

	// ignre first 2 fields - time and pollme
	for (c=2; c<STATCNT; c++) 
	  if (stat[c]) {c=0; break; };

	if (time(0) >= (last_stat_time + (c?stat_min_freq:stat_max_freq))) {
	  print_stat();
	};

	if (this_sess_expire && (this_sess_expire < time(0))) {
	  sio_write(SIO_WARN, "The session has expired - forcing RESET condition...");
	  evt_enqueue(EVTCMD_RESET);
	  this_sess_expire = time(0) + 10; // reset every 10 seconds until done...
	};

    c = ser_getc(srh, 1000); // 1 second for message...
	if (c == -2) {
	  stat[STAT_NOLINK]++;
	  continue;
	};
    if ((c & 0x100) == 0) {
	  stat[STAT_JUNK]++;
      continue;
    };

    if ((c==0x133) || (c==0x10B)) {
      int c1 = ser_getc(srh, MSG_TOUT);
	  if (c1==-2) { stat[STAT_TIMEOUT]++; continue; };
      if (c1!=(c&0xFF)) {
		stat[STAT_MALFORMED]++;
		stat[STAT_POLLOTH]++;
		continue;
      };
      c1 = ser_getc(srh, MSG_TOUT);
	  if (c1==-2) { continue; };
      if (c1!=0x00) {  // not an ACK
		ser_ungetc(srh, c1);
      };
      continue;
    };

    char cmd[37];
    char resp[37];
    int resp_len; // -1 = not handled
    int cmdlen;
    char csum;

    cmdlen = 1;
    cmd[0] = c;
    resp_len = -12; // -12 = no ack + badmsg
    csum = c; // command checksum
    
    while (cmdlen<36) {
      int c1 = ser_getc(srh, MSG_TOUT);
	  if (c1==-2) { stat[STAT_TIMEOUT]++; continue; };
      if (c1 & 0x100) {
		ser_ungetc(srh, c1);
		break;
      };
      cmd[cmdlen] = c1;
      if ((c1&0xFF)==(csum&0xFF)) {
		resp_len = 0;
		int rvc = csd_command(cmd, cmdlen, resp, resp_len);
		if (rvc == CMD_OK) break;
		else {
		  resp_len = -1;
		  if (rvc != CMD_MORE) { cmdlen++; break; };
		};
      };
      csum+=c1;
      cmdlen++;
    };

    
    if (resp_len != -1) {
      char csum = 0;
      for (int i=0; i<resp_len; i++) {
		csum += resp[i];
      };
      while (1) {
		// write response
		ser_write9(srh, 0, resp, resp_len);
        // write checksum/ack
		ser_write9(srh, 1, &csum, 1);
		// wait for Ack if needed
		if (resp_len == 0) { 
		  break;
		};
		int c1 = ser_getc(srh, MSG_ACK_TOUT);
		if (c1==-2) { stat[STAT_NOACK]++; continue; };
		if ((c1==0x00)||(c1=0x100)) break;
		if (c1 & 0x100) {
		  ser_ungetc(srh, c1);
		  break;
		};
      };
    } else if (resp_len != -1){
	  stat[STAT_BADMSG]++;
	  stat[STAT_BADMSGLEN] += cmdlen;

	  char bf[1024];
	  sprintf(bf, "%.3X:", c&0x1FF);
	  for (int i=0; i<cmdlen; i++) {
		if (strlen(bf)>(sizeof(bf)-16)) {
		  strcat(bf, "..."); break;
		};
		sprintf(strchr(bf, 0), ":%.2X", cmd[i]&0x1FF);
	  };	  
	  sio_write(SIO_DEBUG, "BADCMD\t%s", (int)bf);
	  // print c&0xFF, cmd[0..cmdlen-1]
	};
  };
  print_stat();
  ser_close(srh);
  sio_close(stop_num, "Signal Recieved");
};


