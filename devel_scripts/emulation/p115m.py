import os
import sys
import shutil
import struct
import grp
import stat
import select
from termios import tcgetattr, tcsetattr, ECHO, ICANON, VMIN, VTIME, ICRNL, \
    TCSANOW, ISIG, ONLCR
from collections import namedtuple
from threading import Thread, Lock
from bitstruct import pack, unpack
from serial import SerialDevice, writestr, writeln, readline, b2str, tobytes, SerialDeviceLocked

class P115Exception(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self._message = msg

class P115MalformedCmd(P115Exception):  pass
class P115NYI(P115Exception):  pass
class P115ReturnCoin(P115Exception):
    def __init__(self, coin, msg):
        P115Exception.__init__(self, msg)
        self._coin = coin
class P115TryAgain(P115Exception):  pass

def ahex2b(s):
    """ Convert a string of 2 char ASCII HEX to bytearray
    """
    assert len(s) % 2 == 0
    return bytearray([int(s[i*2:i*2+1], 16) for i in range(0, int(len(s)/2))])

def b2ahex(bs):
    """ Convert an iterable of byte-sized ints into a 2char ASCII HEX
        string with spaces. (According ot manual PC should ignore spaces)
    """
    for b in bs:    assert (0 <= b and b <= 0xff)
    return ' '.join(['%02X' % b for b in bs])

class P115Master(SerialDevice):
    POWERON_STR="***** JCA P115 PC-MDB Interface V4.0 *****"

    # Coin Changegiver Configuration TODO: Set it from real config
    coin_values = [0.05, .10, .25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    tube_sizes = [0x10, 0x10, 0x10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    WORD_BSET='u1'*len(coin_values)
    coin_routing = [ (1 if x != 0 else 0) for x in coin_values ]
    coin_to_type = { v:i for (i,v) in enumerate(coin_values) if v != 0 }
    type_to_coin = { v:k for k, v in coin_to_type.items() }

    # Bill Reader Configuration TODO: Set it from real config
    bill_values = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    bill_to_type = { v:i for (i,v) in enumerate(bill_values) if v != 0 }
    type_to_bill = { v:k for k, v in bill_to_type.items() }
    stacker_size = 500
    escrow_capable = True

    # Some protocol metadata to ease message parsing
    TWO_LETTER_CMDS = ['R', 'S', 'T', 'P', 'E', 'D', 'K' ]
    CMD_PAYLOAD_LEN = {
        # Coin Changer Commands
        'R1':   0,
        'S1':   0,
        'S2':   0,
        'S3':   0,
        'S4':   0,
        'T1':   0,
        'T2':   0,
        'N':    4,
        'M':    4,
        'G':    4,
        'P1':   0,
        'E1':   0,
        'D1':   0,
        # Bill Reader Commands
        'R2':   0,
        'S5':   0,
        'S6':   0,
        'S7':   0,
        'S8':   0,
        'L':    4,
        'J':    4,
        'V':    4,
        'P2':   0,
        'E2':   0,
        'D2':   0,
        'K1':   0,
        'K2':   0,
        'Q':    0,
    }

    @staticmethod
    def checkCmdWidth(buf):
        l = 1
        if (buf[0] in P115Master.TWO_LETTER_CMDS):  l += 1
        l = l + P115Master.CMD_PAYLOAD_LEN[buf[0:l]]
        assert len(buf) == l,\
            "Command '%s' wrong length. Expected %d chars" % (buf, l)

    def __init__(self, slave_path):
        SerialDevice.__init__(self, slave_path)
        assert(len(self.coin_values) == 16)

        # Coin changer dynamic state
        self._tube_counts = [ 0 for x in self.coin_values ]
        self._collected_counts = [ 0 for x in self.coin_values ]
        self._coin_evt_q = []
        self._resetCoinConfiguration()

        # Bill Reader dynamic state 
        self._bill_evt_q = []
        self._escrow = None
        self._stacker = []
        self._resetBillConfiguration()
        writeln(self._mFd, self.POWERON_STR)

    def _resetCoinConfiguration(self):
        # TODO: What happens to the coin event queue on reset?
        # TODO: Check default settings for coin enable/disable
        self._coinEnabled = False;
        self._coinEventMode = False;
        self._coin_acceptance_enable = [ True for x in self.coin_values]
        self._coin_dispense_enable = [ True for x in self.coin_values]
        self._coin_acceptance_enable_candidate = [ True for x in self.coin_values]
        self._coin_dispense_enable_candidate = [ True for x in self.coin_values]

    def _resetBillConfiguration(self):
        # TODO: What happens to the bill event queue on reset?
        # TODO: Check default settings for bill enable/disable

        self._billEnabled = False
        self._billEventMode = False
        self._bill_acceptance_enable = [ True for x in self.bill_values]
        self._bill_acceptance_enable_candidate = [ True for x in self.bill_values]
        self._bill_escrow = [ True for x in self.bill_values]
        self._bill_escrow_canidate = [ True for x in self.bill_values]
        self._bill_security = [ True for x in self.bill_values]

    # External events and callbacks
    @SerialDeviceLocked
    def billInput(self, bill):
        if (self._escrow != None):
            raise P115TryAgain("Another bill is in escrow")

        billType = self.bill_to_type[bill]

        if (not self._bill_acceptance_enable[billType]):
            self.send_bill_event('Q4', b2ahex([billType]))
            return

        if  (self.escrow_capable and self._bill_escrow[billType]):
            # Do Escrow
            self._escrow = billType
            self.send_bill_event('Q1', b2ahex([billType]))
        else:
            # No Escrow. TODO: Do we still send a Q1 event here?
            self._stacker.append(billType)
            self.send_bill_event('Q2', b2ahex([billType]))

    def returnBill(self, bill): # Callback when a bill is returned
        raise P115NYI("Must Override this callback")

    @SerialDeviceLocked
    def coinInput(self, coin):
        coinType = self.coin_to_type[coin]
        try:
            if (not self._coinEnabled):
                raise P115ReturnCoin(coin, "All coin accepting disabled")
            if (not self._coin_acceptance_enable[coinType]):
                raise P115ReturnCoin(coin, "Coin accepting for %f is disabled" % coin)

            if (self._tube_counts[coinType] < self.tube_sizes[coinType]):
                # If we have space in the tubes - put it in the tubes
                self._tube_counts[coinType] += 1
            else:
                # Otherwise in the collection bin
                self._collected_counts[coinType] += 1
            self.send_coin_event('P1', b2ahex([coinType]))
        except P115ReturnCoin as e:
            self.send_coin_event('P2', b2ahex([coinType]))
            raise e;

    # Event Handling
    def send_event(self, evt, payload, waitForPoll, evt_q):
        if (waitForPoll):
            evt_q.append((evt, payload))
        else:
            writeln(self._mFd, evt + ' ' + payload)

    def send_coin_event(self, evt, payload):
        self.send_event(evt, payload, not self._coinEventMode, self._coin_evt_q)

    def send_bill_event(self, evt, payload):
        self.send_event(evt, payload, not self._billEventMode, self._bill_evt_q)

    def do_work(self):
        # Lock already acquired
        # Read P115 Master commands
        l = readline(self._mFd)

        print ("RECV[%d]:" % len(l), l)
        sys.stdout.flush()

        l = l.decode('ascii') # All P115M Communication is ASCII
        l = l[:-1] # Skip <cr> at the end
        l = ''.join([x for x in l if x != ' ']) # P115M Ignores whitespace
        P115Master.checkCmdWidth(l)
        writestr(self._mFd, '\x0a') #ACK

        # Coin changer commands
        if (l == 'R1'): # Reset coin acceptor & disable acceptance
            self._resetCoinConfiguration();
            writeln(self._mFd, 'Z') #Respond
            self.send_coin_event('I1', '')
        elif (l == 'S1'): # Get Coin Values for 15 coin types
            writeln(self._mFd, 'S1 ' + b2ahex([(int(100*x)) for x in self.coin_values]))
        elif (l == 'S2'): # Get Scaling Factor (8 bytes) and decimal points (8 bytes)
            writeln(self._mFd, 'S2 01 02')
        elif (l == 'S3'): # Get Coin Routing
            packedRouting = pack(*([self.WORD_BSET] + list(reversed(self.coin_routing))))
            writeln(self._mFd, 'S3 ' + b2ahex(packedRouting))
        elif (l == 'S4'):
            # Get Remaining Information About Config. HW Level (8 bits - hardcoded to 3), BCD
            # encoded Tel. Code for Country for which machine is configured.
            # (16bits - hardcoded to US - 001)
            writeln(self._mFd, 'S4 03 00 01')
        elif (l == 'T1'): # Check for tube full conditions
            tubeFull = [ int(self._tube_counts[i] >= self.tube_sizes[i] and self.tube_sizes[i] != 0)
                for i in range(len(self._tube_counts)) ]
            packedFull = pack(*([self.WORD_BSET] + list(reversed(tubeFull))))
            writeln(self._mFd, 'T1 ' + b2ahex(packedFull))
        elif (l == 'T2'): # Get Tube Counts
            writeln(self._mFd, 'T2 ' + b2ahex(self._tube_counts))
        elif (l[0] == 'N'): # Individual Coin Dispense Enable
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, ahex2b(l[1:]))))))
            assert(len(bset) == 16)
            self._coin_dispense_enable_candidate = bset
            writeln(self._mFd, 'Z')
        elif (l[0] == 'M'): # Individual Manual Dispense Enable
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, ahex2b(l[1:]))))))
            assert(len(bset) == 16)
            self._coin_acceptance_enable_candidate = bset
            writeln(self._mFd, 'Z')
        elif (l[0] == 'G'): # Dispense Coins
            # TODO: Do we check for Individual Coin Dispense Disable here?
            typ = int(l[1:2], 16)
            cnt = int(l[3:4], 16)

            if (typ < 0 or typ > 0xf or cnt < 0 or cnt > 0xf):
                raise P115MalformedCmd("Bad G command: Coin Type/Count are between 0 and 0xF")

            writeln(self._mFd, 'Z')

            if not self._coinEnabled:
                raise P115NYI("Dispensing coins (G) when dispensing is disabled")
            elif not self._coin_dispense_enable[typ]:
                raise P115NYI("Dispensing coins (G) when dispensing for that specific column is disabled")
            elif self._tube_counts[typ] < cnt:
                raise P115NYI("Trying to dispense more coins than are available")
            else:
                self._tube_counts[typ] -= cnt
                self.send_coin_event('G', '')
        elif (l == 'P1'): # Poll Coin Changegiver
            if not self._coinEventMode:
                # TODO: Do we drain the queue one event at a time? Or do we bunch them up? For now
                # just send them one at a time
                if len(self._coin_evt_q) > 0:
                    writeln(self._mFd, ' '.join([evt + ' ' + payload
                        for (evt,payload) in self._coin_evt_q]))
                else:
                    writeln(self._mFd, 'Z')
            else:
                raise P115NYI("Calling poll P1 while we are in event mode")
        elif (l == 'E1'): # Enable Coin Acceptance
            self._coin_acceptance_enable = self._coin_acceptance_enable_candidate
            self._coin_dispense_enable = self._coin_dispense_enable_candidate
            self._coinEnabled = True
            self._coinEventMode = True
            writeln(self._mFd, 'Z')
        elif (l == 'D1'): # Disable Coin Acceptance
            self._coinEnabled = False
            self._coinEventMode = False
            writeln(self._mFd, 'Z')
        # Bill Reader Commands
        elif (l == 'R2'): # Reset bill reader & disable acceptance
            self._resetBillConfiguration()
            writeln(self._mFd, 'Z')
            self.send_bill_event('I2', '')
        elif (l == 'S5'): # Bill Values
            writeln(self._mFd, 'S5 ' + b2ahex([(int(100*x)) for x in self.bill_values]))
        elif (l == 'S6'):
            # Hardcoded 16-bit Bill Scaling factor (1) and 8-bit decimal points (2)
            writeln(self._mFd, 'S6 00 01 02')
        elif (l == 'S7'):
            # Stacker Info - escrow capable 00/FF, # bills (2 bytes)
            writeln(self._mFd, 'S7 %s %s' % \
                ('FF' if self.escrow_capable else '00', '%04X' % self.stacker_size))
        elif (l == 'S8'): # Miscelaneous Data
            raise P115NYI("S8 Command NYI")
        elif (l[0] == 'L'): # Individual Bill Accept Enable
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, ahex2b(l[1:]))))))
            assert(len(bset) == 16)
            self._bill_acceptance_enable_candidate = bset
            writeln(self._mFd, 'Z')
        elif (l[0] == 'J'): # Individual Bill Escrow Setting
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, ahex2b(l[1:]))))))
            assert(len(bset) == 16)
            self._bill_escrow_canidate = bset
            writeln(self._mFd, 'Z')
        elif (l[0] == 'V'): # Individual Bill Escrow Setting
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, ahex2b(l[1:]))))))
            assert(len(bset) == 16)
            self._bill_escrow_canidate = bset
            writeln(self._mFd, 'Z')
        elif (l == 'P2'): # Poll Bill Reader
            if not self._billEventMode:
                # TODO: Do we drain the queue one event at a time? Or do we bunch them up? For now
                # just send them one at a time
                if len(self._bill_evt_q) > 0:
                    writeln(self._mFd, ' '.join([evt + ' ' + payload
                        for (evt,payload) in self._bill_evt_q]))
                else:
                    writeln(self._mFd, 'Z')
            else:
                raise P115NYI("Calling poll P2 while we are in event mode")
        elif (l == 'E2'): # Enable Bill Acceptance
            self._bill_acceptance_enable = self._bill_acceptance_enable_candidate
            self._bill_escrow = self._bill_escrow_canidate
            self._billEnabled = True
            self._billEventMode = True
            writeln(self._mFd, 'Z')
        elif (l == 'D2'): # Disable Coin Acceptance
            self._billEnabled = False
            self._billEventMode = False
            writeln(self._mFd, 'Z')
        elif (l == 'K1'): # Stack Bill
            if (self._escrow == None):
                raise P115NYI("K1 With no bill in escrow")
            else:
                self._stacker.append(self._escrow)
                self._escrow = None
                writeln(self._mFd, 'Z')
        elif (l == 'K2'): # Return Bill
            if (self._escrow == None):
                raise P115NYI("K2 With no bill in escrow")
            else:
                self.returnBill(self._escrow)
                billType = self._escrow
                self._escrow = None
                writeln(self._mFd, 'Z')
                self.send_bill_event('Q4', b2ahex([billType]))
        elif (l == 'Q'): # Stacker Status - Full/Not Full + # of bills
            nbills = len(self._stacker)
            full = 'F' if nbills >= self.stacker_size else 'N'
            writeln(self._mFd, 'Q %s %s' % (full, nbills))
        else:
            print ("Malformed command: ", l)
            raise P115MalformedCmd(l)
