#!/usr/bin/env python3.4
"""serial_shell, - simple serial shell for talking to a serial device directly. Mostly does pretty printing and allows for easy encoding of non-ascii charaters using hex.

Usage:
  serial_shell.py [--device=<dev>] [--noline]
  serial_shell.py (-h | --help)
  serial_shell.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --device=<dev>            Path to /dev node corresponding to P115M. [default: /dev/mdb] 
  --noline                  Don't wait for new line to display characters as they appear
"""

import sys
import os
import cmd2
from docopt import docopt
from serial import readline, writeln, _setupPair
from threading import Thread
from select import select
from errno import *
import string

args = docopt(__doc__, version="WTF")

# Devices
serial_fd = None
printable = set(map(ord, set(string.printable) - set(string.whitespace)))

noline = args['--noline']

def ppb(b):
    if b in printable:
        return "%02c " % chr(b)
    else:
        return "%02x " % b

def hexbs(s):
    return ''.join(["%02x " % x for x in s])

def ppbs(s):
    return ''.join(map(ppb, s))

class SerialShell(cmd2.Cmd):
    def do_cmd(self, line):
        print ("SEND:[%d]: %s" % (len(line), line))
        writeln(serial_fd, line)

    def do_xcmd(self, line):
        els = line.split(' ')
        line = ''
        for x in els:
            if (x.startswith('0x')):
                line += chr(int(x, 16))
            else:
                line += x

        print ("SEND:[%d]: %s" % (len(line), line))
        writeln(serial_fd, line)

done = False
def lineReaderThr(fd):
    while (not done):
        s, dummy1, dummy2 = select([fd], [], [], 1)
        if (fd in s):
            
            l =readline(fd)
            print ("RECV[%03d]: %s" %(len(l), hexbs(l)))
            print ("           %s" %ppbs(l))

def rawReaderThr(fd):
    while (not done):
        s, dummy1, dummy2 = select([fd], [], [], 1)
        if (fd in s):
            l = bytes('', 'ascii')
            while 1:
                try:
                    c = os.read(fd, 1)
                    l += c
                except IOError as e:
                    if e.errno == EAGAIN:
                        break
                    else:
                        raise e
                
            print ("RECV[%03d]: %s" %(len(l), hexbs(l)))

try:
    serial_fd = os.open(args['--device'], (os.O_RDWR | os.O_NOCTTY | (os.O_NONBLOCK if noline else 0)))
    _setupPair(serial_fd, serial_fd)
except OSError as e:
    print ("Couldn't open %s: %s" % (args['--device'], str(e)))
    sys.exit(-1)

try:
    t = Thread(target=(rawReaderThr if noline else lineReaderThr), args=[serial_fd])
    t.start()
    sys.argv=[sys.argv[0]]
    shell = SerialShell()
    shell.cmdloop()
finally:
    done = True
    os.close(serial_fd)
    t.join();
