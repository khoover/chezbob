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

dialout = grp.getgrnam("dialout")

def _disableFlag(fd, ind, flag):
    attrs = tcgetattr(fd)
    attrs[ind] = attrs[ind] & ~flag
    tcsetattr(fd, TCSANOW, attrs)

def _setCCFlag(fd, ind, val):
    attrs = tcgetattr(fd)
    attrs[6][ind] = val 
    tcsetattr(fd, TCSANOW, attrs)

def _setupPair(m, s):
    for fd in [m,s]:
        _disableFlag(fd, 3, (ECHO|ICANON|ISIG))
        _disableFlag(fd, 0, (ICRNL))
        _setCCFlag(fd, VMIN, 1)
        _setCCFlag(fd, VTIME, 0)
    _disableFlag(s, 1, ONLCR)

def writestr(fd, s):
  os.write(fd, bytes(s, "ascii"))

def writeln(fd, s):
  if (type(s) == bytes):
    os.write(fd, s + bytes([0xd]))
  else:
    writestr(fd, s+'\x0d')

def readline(fd):
    res = b''
    while 1:
      b = os.read(fd, 1)
      res += b

      if (b == b'\x0d'):
        return res

def b2str(b):   return bytes.decode(b, 'ascii')
def tobytes(arg):
    if (type(arg) == str):
        return bytes(arg, 'ascii')
    elif (type(arg) == bytes):
        return arg
    else:
        assert False

class SerialDevice:
    """ A Fake Serial Device consists of:
        - a pseudo-terminal used for communicating with driver
        - main loop (in a separate thread) responding to commands
        - provides functions to simulate external (hardware events)
        Everything is synchronized by a single lock L. Taking L is required both to
        update the state of the device and to write over its serial port.
    """
    def __init__(self, slave_path):
        # Create pty for communicating with driver
        self._mFd, self._sFd = os.openpty();
        _setupPair(self._mFd, self._sFd)
        # Symlink the slave end of pty to desired /dev node
        self._slavePath = slave_path
        name = os.ttyname(self._sFd)
        os.symlink(name, slave_path)
        os.lchown(slave_path, 0, dialout.gr_gid)
        os.chown(slave_path, 0, dialout.gr_gid)
        os.chmod(slave_path, stat.S_IRWXU | stat.S_IRWXG)

        # Another pipe for pining the main loop
        self._rPingFd, self._wPingFd = os.pipe()
        # Synchronization and launch loop
        self._L = Lock();
        self._done = False
        self._thr = Thread(target=self.main_loop, args=[])
        self._thr.start();

    def slave(self):
        return self._slavePath

    def write(self, byteArr):
        os.write(self._mFd, byteArr)

    def cleanup(self):
        self._done = True
        self.ping_main_loop()
        self._thr.join()
        os.unlink(self._slavePath)

    def ping_main_loop(self):
        writeln(self._wPingFd, "ping")

    def lock(self): self._L.acquire()
    def unlock(self): self._L.release()

    def main_loop(self):
        while (not self._done):
            readSet, writeSet, xtrSet = select.select([self._mFd, self._rPingFd], [], [])
            # Read exernal events
            if (self._rPingFd in readSet):
                assert (os.read(self._rPingFd, 5) == b'ping\x0d')
            if (self._mFd in readSet):
                self.lock()
                try:
                    self.do_work();
                finally:
                    self.unlock()

    def do_work(self):
        raise Exception("NYI")
