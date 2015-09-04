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

class P115NYI(P115Exception):  pass

# The P115Slave speaks the CardLink Protocol with the PC.
# TODO: Find the manual for this. The current implementation
# just copies what we see in the logs.
class P115Slave(SerialDevice):
    def __init__(self, slave_path):
        SerialDevice.__init__(self, slave_path)
        self._request_col = None

    def do_work(self):
        # Lock already acquired
        # Read P115 Master commands
        self.unlock()
        l = readline(self._mFd)
        self.lock()
        l = l.decode('ascii') # All comm seems to be ASCII
        l = l.strip() # Screw \r and \n
        #l = ''.join([x for x in l if x != '\n']) # Screw ACKs

        writestr(self._mFd, '\x0a') #ACK

        if l == '':
            pass # The \n\n\n\n\r at the begining. Don't care.
        elif l == '\x1B':  # Reset request + bootup string
            writeln(self._mFd, '* P208 Reset')
            writeln(self._mFd, '*M 30 P208 v1.11 (c)2013 JCA Systems Ltd')
        elif l == 'W090001': # WTF1 ?
            writeln(self._mFd, 'F')
        elif l == 'W070001': # WTF2 ?
            writeln(self._mFd, 'F')
        elif l == 'WFF0000': # WTF3 ?
            writeln(self._mFd, 'G')
        elif l == 'X': # WTF3 ?
            pass # ACK. Don't care
        elif l == 'A': # Request Authorized
            assert(self._request_col != None)
            self.authorized(self._request_col)
            self._request_col = None
        elif l == 'D': # Request Denied
            assert(self._request_col != None)
            self.denied(self._request_col)
            self._request_col = None
        else:
            print ("Unknown command |%s|" % l)
            raise P115NYI("Unknown command: %s " % l)

    @SerialDeviceLocked
    def request_auth(self, col):
        self._request_col = col;
        writeln(self._mFd, 'R       %02d' % col)

    @SerialDeviceLocked
    def vend_ok(self):
        writeln(self._mFd, 'K')

    @SerialDeviceLocked
    def vend_failed(self):
        writeln(self._mFd, 'L')

    def authorized(self, col):
        raise P115NYI("Must override")

    def denied(self, col):
        raise P115NYI("Must override")
