#ifndef _VMCSERV_H_
#define _VMCSEV_H_


#define VERSION		"1.39"


//
//
//                         VMC COMMAND INTERFACE
//
//

#define CMD_OK          1        // command was completely recieved and executed
#define CMD_MORE        2        // command incomplete
#define CMD_NOTSUPPORT  3        // command not supported
#define CMD_FAIL   -1            // command makes no sense

// parse the commands. returns one of CMD_ constants
//  cmd - the recieved data. first byte is address byte
//  cmdlen - length of command (excluding last byte - checksum)
// resp is only used if RV is CMD_OK
//  resp - reponse buffer. big enough for any MDB packet
//  resplen - response length.  0 = default - ACK only,
//                >0 - that many databytes (CS is automatic)
int csd_command(char * cmd, int cmdlen, char * resp, int & resplen);
void csd_init();
int csd_onidle();

// enququ command to send to machine
#define EVTCMD_RESET         0
#define EVTCMD_BEGINSESS     3   // arg is avail. money
#define EVTCMD_APPROVED      5
#define EVTCMD_DENIED        6  
//#define EVTCMD_CANCEL        4
#define EVTCMD_CANCELSESS    4   // sent by user to cancel session
#define EVTCMD_ENDSESS       7   // sent internally only

#define EVTCMD_STATUS         -2  // pseudocommand

void evt_enqueue(int event_, int param_=0);

//
//
//                         STATISTICS MODULE
//
//

#define STAT_TIME       0

#define STAT_POLLME     1
#define STAT_MSGME      2
#define STAT_POLLRV     3
#define STAT_POLLOTH    4

#define STAT_NOLINK     5
#define STAT_TIMEOUT    6
#define STAT_NOACK      7

#define STAT_JUNK       8
#define STAT_BADMSG     9
#define STAT_BADMSGLEN  10
#define STAT_MALFORMED  11
#define STAT_RESETOTH	12

#define STATCNT         13

#ifdef VMCSERV_C
int stat[STATCNT];
int stat_total[STATCNT];
char * statnames[STATCNT] = {
  "TIME",                // seconds since last stat() printing

  "Poll-me",             // polls to casheless - should be going up constantly
  "Msg-me",              // all messages to me except polls
  "Poll-rv",             // pol message was called, and it returned not IDLE
  "Discovery",           // POLLOTH - polls to changer,acceptor

  "!Nolink",             // timeout reading first byte - is link not connected?
  "!Timeout",            // timeout reading packet data - the link was broken in mid-message?
  "!noAck",              // timeout waiting for message's ACK

  "!Junk",               // junk - after packet end, before packet start
  "!BadMsg",             // bad messages - count 
  "!BadMsgLen",          // bad messages - length
  "!Malformed",          // malformed message count
 
  "ResetOth",            // RESET message to changer/acceptor
};
#else 
extern int stat[STATCNT];
extern int stat_total[STATCNT];
#endif


#endif
