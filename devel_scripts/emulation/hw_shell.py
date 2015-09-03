#!/usr/bin/env python3.4
"""hw_shell, the fake hardware shell

Usage:
  hw_shell.py [--simulate-p115m] [--simulate-barcode] [--p115m-device=<mdb_dev>]
  hw_shell.py (-h | --help)
  hw_shell.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --simulate-p115m          Should we simulate p115m (if not, we can still
                            issue VDB commands to the real hardware)
  --simulate-barcode        Should we simulate the barcode scanner (shouldn't
                            simulate when we have a real barcode scanner attached)
  --p115m-device=<mdb_dev>  Path to /dev node corresponding to P115M. [default: /dev/mdb] 
"""

import sys
import os
import cmd2
from docopt import docopt
from serial import readline, writeln, _setupPair
from p115m import FakeBarcodeScanner, P115Master, P115ReturnCoin

args = docopt(__doc__, version="WTF")

# Devices
barcode = None
mdb = None
def hexs(s):
    return ''.join(["%02d " % ord(x) for x in s])

def hexb(s):
    return ''.join(["%02d " % x for x in s])

class HWShell(cmd2.Cmd):
    if args['--simulate-p115m']:
        def do_put_coin(self, line):
            try:
                mdb.coinInput(float(line))
                print ("Ok")
            except (ValueError, AssertionError):
                print ("Error: Not a valid coin - %s" % line)
            except P115ReturnCoin as e:
                print ("Coin Returned: %s" % e._message)

        def do_press_coin_return(self, line):
            mdb.pressCoinReturn()
            print ("Ok")
                
    if args['--simulate-barcode']:
        def do_scan(self, line):
            print (line);

try:
    mdb_dev = args['--p115m-device']
    if args['--simulate-barcode']:
        barcode = FakeBarcodeScanner("/dev/barcode");
    if args['--simulate-p115m']:
        mdb = P115Master(mdb_dev);

    sys.argv=[sys.argv[0]]
    shell = HWShell()
    shell.cmdloop()
except Exception(e):
    print (e)
    raise e
finally:
    if args['--simulate-barcode']:
        barcode.cleanup();
    if args['--simulate-p115m']:
        mdb.cleanup();
