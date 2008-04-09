#ifndef _MDBSERV_H_
#define _MDBSERV_H_


#define VERSION   "2.12"

#ifndef MDBEXT
#define MDBEXT extern
#endif


//
//
//             MDBSERV.CPP
//
//

// both 'where' and 'msg' could contain printf-specifiers for i1..i3
int report_fail(char * where, int code=0, const char * msg = 0, int i1=0, int i2=0, int i3=0);
bool strbegins(char * slong, char * sshort);

int ascii_to_hex1(char c);
int ascii_to_hex2(char * cc);


// send_command
//   send string in "cmd"
//   wait up to timeout ms for response
//   returns -2 on timeout, -1 on error (link or protocol), 1 if response recieved 
// when expect==NULL, the parsed answer is stored into "resp" buffer as following:
//   resp[0] - first response character unchanged
//   resp[1] - second nonspace response character unchager when resp[0] in P,Q,I
//   resp[...]  - hex-decoded rest of the strings (up to resp[resplen-1])
//   rest of resp is filld with 0's - always 
// when expect!=NULL, it must match coresponding resp characters, and those charactes would be 
// removed from resp.
// the "X" codes are always parsed and handled as an error
int send_command(const char * cmd, char* expect=0, int timeout = 1000);

// response code for send_command
MDBEXT unsigned char resp[64];
MDBEXT int  resplen;
MDBEXT char resp_raw[255];  // raw string (ASCII only, no nonprintables)

//
//
//                    MDBLOGIC.CPP
//
//

// process message that did not come as a command response
//  bf is guaranteed to have 4 null characters after bfsize
// in mdblogic.cpp
int on_poll(char * bf, int bfsize);

void cash_reset();

// forceprint:
//   0 print if changed
//   1 print always
//   -1 print as changed, do not scan tube full
int cc_tube_refresh(int forceprint);

// init coinchanger
//   returns -1 on error or timeout, or 0 if init  ok and all ready
// also sets cc_ready
int cc_init();

// poll the coinchanger
int cc_poll();

int bb_stacker_refresh(int forceprint);

// init bill acceptor
//   returns -2 on timeout, -1 on error, or 0 if init  ok and all ready
// also sets bb_ready
int bb_init();

int bb_poll();

// accept/reject stuff in escrow
int cash_accept(bool accept, int amt=0);

// give given number of coins of this type
// RV is number of coins given sucessfully
//  or -1/-2 if error occur before first coin was given
// it also decreases escrow amount if it can, and sends -ESCROW messages as it does so
int giveout_coins(int type, int count);

// gives given amount using availible coins of higest denomination
// RV is amount given sucessfully
//  or -1/-2 if error occur before first coin was given
// uses giveout_coins with all of its side effects
int giveout_smart(int amount);


// notify of escrow change. should be the only thing that changes the var except reset
void escrow_change(char * trans, int ptype, int amount);

MDBEXT SER_HANDLE srh;


// the enabling mask
// will auto-enable devices when they go online
//   bit 0 (1)   - enable coins
//   bit 1 (2)   - enable bill validaor
MDBEXT int want_enabled;

// changegiver settings (filled at coin_init() )
MDBEXT int cc_ready;       // 0 = not ready, 1 = ready/disabled, 2 = ready/enabled
MDBEXT int cc_values[16];  // coin values, scaled to cents
MDBEXT bool cc_full[16];   // tube full status
MDBEXT int cc_count[16];   // coin count in each tube
MDBEXT int cc_mandisp[16]; // min # of coins i the tube for dispensing to be enabled
MDBEXT int cc_man_ok;      // set of tubes where manual dispensing was allowed (bitarray)

// bill validator settings (filled at bval_init() )
MDBEXT int bb_ready;       // 0 = not ready, 1 = ready/disabled, 2 = ready/enabled
MDBEXT int bb_values[16];  // bill values, scaled
MDBEXT int bb_capacity;    // bill stacker capacity
MDBEXT int bb_stacked;     // bills stacked
MDBEXT bool bb_full;       // true = bill stacker full

// virtual escrow settings
MDBEXT int esc_total;      // total amount of money in the escrow
MDBEXT int esc_coins[16];  // coint for each coin type
MDBEXT int esc_bill;       // bb escrow: 0 if empty, 100+billnum otherwise


#endif
