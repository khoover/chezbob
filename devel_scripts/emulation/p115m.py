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
from serial import SerialDevice, writestr, writeln, readline, b2str, tobytes

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
    TWO_LETTER_RESP = ['S', 'T']
    TWO_LETTER_EVTS = ['P']
    CMD_PAYLOAD_LEN = {
        # Coin Changer Commands
        'R1':   0,
        'S1':   0,
        'S2':   0,
        'S3':   0,
        'S4':   0,
        'T1':   0,
        'T2':   0,
        'N':    2,
        'M':    2,
        'G':    2,
        'P1':   0,
        'E1':   0,
        'D1':   0,
        # Bill Reader Commands
        'R2':   0,
        'S5':   0,
        'S6':   0,
        'S7':   0,
        'S8':   0,
        'L':    2,
        'J':    2,
        'V':    2,
        'P2':   0,
        'E2':   0,
        'D2':   0,
        'K1':   0,
        'K2':   0,
        'Q':    0,
    }

    @staticmethod
    def read(fd, twoLetrTbl, payloadTbl):
        cmd = os.read(fd, 1)
        if b2str(cmd) in twoLetrTbl:
            cmd += os.read(fd, 1)

        payloadLen = payloadTbl[b2str(cmd)]

        if (payloadLen > 0):
            for i in range(0, payloadLen):
                cmd += os.read(fd, 1)

            cr = os.read(fd, 1)
            assert(cr == b'\x0d')
        else:
            while True:
                c = os.read(fd, 1)
                if (c == b'\x0d'):  break;
                cmd += c

        return cmd

    @staticmethod
    def readCmd(fd):
        return P115Master.read(fd, P115Master.TWO_LETTER_CMDS, P115Master.CMD_PAYLOAD_LEN)

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

        self.lock()
        writeln(self._mFd, self.POWERON_STR)
        self.unlock()

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
    def billInput(self, bill):
        try:
            self.lock()
            if (self._escrow != None):
                raise P115TryAgain("Another bill is in escrow")

            billType = self.bill_to_type[bill]

            if (not self._bill_acceptance_enable[billType]):
                self.send_bill_event('Q4', chr(billType))
                return

            if  (self.escrow_capable and self._bill_escrow[billType]):
                # Do Escrow
                self._escrow = billType
                self.send_bill_event('Q1', chr(billType))
            else:
                # No Escrow. TODO: Do we still send a Q1 event here?
                self._stacker.append(billType)
                self.send_bill_event('Q2', chr(billType))
        finally:
            self.unlock()

    def returnBill(self, bill): # Callback when a bill is returned
        raise P115NYI("Must Override this callback")

    def coinInput(self, coin):
        coinType = self.coin_to_type[coin]

        try:
            self.lock()
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
            self.send_coin_event('P1', chr(coinType))
        except P115ReturnCoin as e:
            self.send_coin_event('P2', chr(coinType))
            raise e;
        finally:
            self.unlock()

    # Event Handling
    def send_event(self, evt, payload, waitForPoll, evt_q):
        if (waitForPoll):
            evt_q.append((evt, payload))
        else:
            writeln(self._mFd, evt + payload)

    def send_coin_event(self, evt, payload):
        self.send_event(evt, payload, not self._coinEventMode, self._coin_evt_q)

    def send_bill_event(self, evt, payload):
        self.send_event(evt, payload, not self._billEventMode, self._bill_evt_q)

    def do_work(self):
        # Lock already acquired
        # Read P115 Master commands
        l = self.readCmd(self._mFd)
        print ("RECV[%d]:" % len(l), l)
        sys.stdout.flush()
        writestr(self._mFd, '\x0a') #ACK
        # Coin changer commands
        if (l == b'R1'): # Reset coin acceptor & disable acceptance
            self._resetCoinConfiguration();
            writeln(self._mFd, 'Z') #Respond
            self.send_coin_event('I1', '')
        elif (l == b'S1'): # Get Coin Values for 15 coin types
            s = bytes("S1",'ascii') + bytes([(int(100*x)) for x in self.coin_values])
            writeln(self._mFd, s)
        elif (l == b'S2'): # Get Scaling Factor (8 bytes) and decimal points (8 bytes)
            s = bytes("S2",'ascii') + bytes([0x1, 0x2])
            writeln(self._mFd, s)
        elif (l == b'S3'): # Get Coin Routing
            s = bytes("S3",'ascii') + pack(*([self.WORD_BSET] + list(reversed(self.coin_routing))))
            writeln(self._mFd, s)
        elif (l == b'S4'):
            # Get Remaining Information About Config. HW Level (8 bits - hardcoded to 3), BCD
            # encoded Tel. Code for Country for which machine is configured.
            # (16bits - hardcoded to US - 001)
            s = bytes("S4", 'ascii') + bytes([0x3, 0x0, 0x1])
            writeln(self._mFd, s)
        elif (l == b'T1'): # Check for tube full conditions
            tubeFull = [ int(self._tube_counts[i] >= self.tube_sizes[i])
                for i in range(len(self._tube_counts)) ]

            s = bytes("T1", 'ascii') + pack(*([self.WORD_BSET] + list(reversed(tubeFull))))
            writeln(self._mFd, s)
        elif (l == b'T2'): # Get Tube Counts
            s = bytes("T2",'ascii') + bytes(self._tube_counts)
            writeln(self._mFd, s)
        elif (l[0] == ord('N')): # Individual Coin Dispense Enable
            if len(l) != 3:
                raise P115MalformedCmd("Bad N command: Expected 2 bytes afterwards")
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, l[1:])))))
            self._coin_dispense_enable_candidate = bset
            writeln(self._mFd, 'Z')
        elif (l[0] == ord('M')): # Individual Manual Dispense Enable
            if len(l) != 3:
                raise P115MalformedCmd("Bad M command: Expected 2 bytes afterwards")
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, l[1:])))))
            self._coin_acceptance_enable_candidate = bset
            writeln(self._mFd, 'Z')
        elif (l[0] == ord('G')): # Dispense Coins
            # TODO: Do we check for Individual Coin Dispense Disable here?
            if len(l) != 3:
                raise P115MalformedCmd("Bad G command: Expected 2 bytes afterwards")
                
            typ = l[1]
            cnt = l[2]

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
        elif (l == b'P1'): # Poll Coin Changegiver
            if not self._coinEventMode:
                # TODO: Do we drain the queue one event at a time? Or do we bunch them up? For now
                # just send them one at a time
                if len(self._coin_evt_q) > 0:
                    buf = bytes('', 'ascii')
                    for (evt, payload) in self._coin_evt_q:
                        buf += tobytes(evt) + tobytes(payload)

                    writeln(self._mFd, buf)
                else:
                    writeln(self._mFd, 'Z')
            else:
                raise P115NYI("Calling poll P1 while we are in event mode")
        elif (l == b'E1'): # Enable Coin Acceptance
            self._coin_acceptance_enable = self._coin_acceptance_enable_candidate
            self._coin_dispense_enable = self._coin_dispense_enable_candidate
            self._coinEnabled = True
            self._coinEventMode = True
            writeln(self._mFd, 'Z')
        elif (l == b'D1'): # Disable Coin Acceptance
            self._coinEnabled = False
            self._coinEventMode = False
            writeln(self._mFd, 'Z')
        # Bill Reader Commands
        elif (l == b'R2'): # Reset bill reader & disable acceptance
            self._resetBillConfiguration()
            writeln(self._mFd, 'Z')
            self.send_bill_event('I2', '')
        elif (l == b'S5'): # Bill Values
            s = bytes("S5",'ascii') + bytes([(int(100*x)) for x in self.bill_values])
            writeln(self._mFd, s)
        elif (l == b'S6'): # Hardcoded Bill Scaling factor (1) and decimal points (2)
            s = bytes("S6",'ascii') + bytes([0x0, 0x1, 0x2])
            writeln(self._mFd, s)
        elif (l == b'S7'): # Stacker Info - escrow capable 00/FF, # bills (2 bytes)
            s = bytes("S7",'ascii') + bytes([(0xFF if self.escrow_capable else 0x00)]) + \
                pack('u16', self.stacker_size)
            writeln(self._mFd, s)
        elif (l == b'S8'): # Miscelaneous Data
            raise P115NYI("S8 Command NYI")
        elif (l[0] == ord('L')): # Individual Bill Accept Enable
            if len(l) != 3:
                raise P115MalformedCmd("Bad L command: Expected 2 bytes afterwards")
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, l[1:])))))
            self._bill_acceptance_enable_candidate = bset
            writeln(self._mFd, 'Z')
        elif (l[0] == ord('J')): # Individual Bill Escrow Setting
            if len(l) != 3:
                raise P115MalformedCmd("Bad J command: Expected 2 bytes afterwards")
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, l[1:])))))
            self._bill_escrow_canidate = bset
            writeln(self._mFd, 'Z')
        elif (l[0] == ord('V')): # Individual Bill Escrow Setting
            if len(l) != 3:
                raise P115MalformedCmd("Bad V command: Expected 2 bytes afterwards")
            bset = list(reversed(list(map(bool, unpack(self.WORD_BSET, l[1:])))))
            self._bill_escrow_canidate = bset
            writeln(self._mFd, 'Z')
        elif (l == b'P2'): # Poll Bill Reader
            if not self._billEventMode:
                # TODO: Do we drain the queue one event at a time? Or do we bunch them up? For now
                # just send them one at a time
                if len(self._bill_evt_q) > 0:
                    buf = bytes('', 'ascii')
                    for (evt, payload) in self._bill_evt_q:
                        buf += tobytes(evt) + tobytes(payload)

                    writeln(self._mFd, buf)
                else:
                    writeln(self._mFd, 'Z')
            else:
                raise P115NYI("Calling poll P2 while we are in event mode")
        elif (l == b'E2'): # Enable Bill Acceptance
            self._bill_acceptance_enable = self._bill_acceptance_enable_candidate
            self._bill_escrow = self._bill_escrow_canidate
            self._billEnabled = True
            self._billEventMode = True
            writeln(self._mFd, 'Z')
        elif (l == b'D2'): # Disable Coin Acceptance
            self._billEnabled = False
            self._billEventMode = False
            writeln(self._mFd, 'Z')
        elif (l == b'K1'): # Stack Bill
            if (self._escrow == None):
                raise P115NYI("K1 With no bill in escrow")
            else:
                self._stacker.append(self._escrow)
                self._escrow = None
                writeln(self._mFd, 'Z')
        elif (l == b'K2'): # Return Bill
            if (self._escrow == None):
                raise P115NYI("K2 With no bill in escrow")
            else:
                self.returnBill(self._escrow)
                billType = self._escrow
                self._escrow = None
                writeln(self._mFd, 'Z')
                self.send_bill_event('Q4', chr(billType))
        elif (l == b'Q'): # Stacker Status - Full/Not Full + # of bills
            nbills = len(self._stacker)
            s = bytes("F" if nbills >= self.stacker_size else "N" ,'ascii') + pack('u16', nbills)
            writeln(self._mFd, s)
        else:
            print ("Malformed command: ", l)
            raise P115MalformedCmd(l)
