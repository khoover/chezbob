import os
import grp
import stat
import select
import fcntl
from termios import tcgetattr, tcsetattr, ECHO, ICANON, VMIN, VTIME, ICRNL, \
    TCSANOW, ISIG, ONLCR
from errno import EAGAIN
from threading import Thread, Lock

dialout = grp.getgrnam("dialout")

def _disableFlag(fd, ind, flag):
    attrs = tcgetattr(fd)
    attrs[ind] = attrs[ind] & ~flag
    tcsetattr(fd, TCSANOW, attrs)

def _setCCFlag(fd, ind, val):
    attrs = tcgetattr(fd)
    attrs[6][ind] = val 
    tcsetattr(fd, TCSANOW, attrs)

def setupFd(fd):
    _disableFlag(fd, 3, (ECHO|ICANON|ISIG))
    _disableFlag(fd, 0, (ICRNL))
    _setCCFlag(fd, VMIN, 1)
    _setCCFlag(fd, VTIME, 0)

def SerialDeviceLocked(f):
    def g(self, *args):
        try:
            self.lock()
            return f(self, *args)
        finally:
            self.unlock()
    return g

class SerialInterrupted(Exception): pass
class SerialNYI(Exception): pass
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
        self._mFd, self._sFd = os.openpty()
        setupFd(self._mFd)
        setupFd(self._sFd)
        _disableFlag(self._sFd, 1, ONLCR)
        # Make _mFd non-blocking
        oldFl = fcntl.fcntl(self._mFd, fcntl.F_GETFL)
        fcntl.fcntl(self._mFd, fcntl.F_SETFL, oldFl & (~os.O_NONBLOCK))
        # Symlink the slave end of pty to desired /dev node
        self._slavePath = slave_path
        name = os.ttyname(self._sFd)
        os.symlink(name, slave_path)
        os.lchown(slave_path, 0, dialout.gr_gid)
        os.chown(slave_path, 0, dialout.gr_gid)
        os.chmod(slave_path, stat.S_IRWXU | stat.S_IRWXG)

        # Synchronization and launch loop
        self._L = Lock()
        self._done = False
        self._thr = Thread(target=self.main_loop, args=[])
        # Open for business
        self._thr.start()

    def write(self, arg):
        if (isinstance(arg, bytes)):
            os.write(self._mFd, arg)
        else:
            assert(isinstance(arg, str))
            os.write(self._mFd, bytes(arg, "ascii"))

    def writeln(self, arg):
        if (isinstance(arg, bytes)):
            self.write(arg + bytes([0xd]))
        else:
            assert(isinstance(arg, str))
            self.write(arg + '\x0d')

    def interruptibleReadline(self):
        res = b''
        while (not self._done):
            self.unlock()
            readSet, _, _ = select.select([self._mFd], [], [], 1)
            self.lock()
            if (self._mFd in readSet):
                while 1:
                    try:
                        b = os.read(self._mFd, 1)
                        res += b

                        if (b == b'\x0d'):
                            return res
                    except IOError as e:
                        if e.errno == EAGAIN:
                            break
                        else:
                            raise e
        # Only way to get here is if _done=True before we finish reading a line
        raise SerialInterrupted()

    def cleanup(self):
        self._done = True
        self._thr.join()
        os.unlink(self._slavePath)

    def lock(self): self._L.acquire()
    def unlock(self): self._L.release()

    def main_loop(self):
        while (not self._done):
            try:
                self._do_work()
            except SerialNYI:
                # Subclass doesn't want to listen for data
                return

    # Implementing classes subclass this..
    @SerialDeviceLocked
    def _do_work(self):
        try:
            self.do_work()
        except SerialInterrupted:
            return

    def do_work(self):
        raise SerialNYI()
