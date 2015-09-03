#!/usr/bin/env python3.4
"""hw_shell, the fake hardware shell

Usage:
  hw_shell.py [--simulate-p115m] [--simulate-soda-barcode] [--p115m-device=<mdb_dev>]
  hw_shell.py (-h | --help)
  hw_shell.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --simulate-p115m          Should we simulate p115m (if not, we can still
                            issue VDB commands to the real hardware)
  --simulate-soda-barcode        Should we simulate the barcode scanner (shouldn't
                            simulate when we have a real barcode scanner attached)
  --p115m-device=<mdb_dev>  Path to /dev node corresponding to P115M. [default: /dev/mdb] 
"""

import sys
import os
import cmd2
from docopt import docopt
from serial import readline, writeln, _setupPair
from p115m import P115Master, P115ReturnCoin, P115TryAgain
from soda_barcode import SodaBarcodeScanner

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
                coin = float(line)
                assert coin in mdb.coin_to_type
                mdb.coinInput(coin)
                print ("Ok")
            except (ValueError, AssertionError):
                print ("Error: Not a valid coin - %s" % line)
            except P115ReturnCoin as e:
                print ("Coin Returned: %s" % e._message)

        def do_press_coin_return(self, line):
            mdb.pressCoinReturn()
            print ("Ok")

        def do_put_bill(self, line):
            try:
                bill = float(line)
                assert bill in mdb.bill_to_type
                mdb.billInput(bill)
                print ("Ok")
            except (ValueError, AssertionError):
                print ("Error: Not a valid bill - %s" % line)
            except P115TryAgain as e:
                print ("Can't put a coin in yet - another coin is in escrow")

    if args['--simulate-soda-barcode']:
        def do_soda_scan(self, line):
            barcode.scan(line.strip())

try:
    mdb_dev = args['--p115m-device']
    if args['--simulate-soda-barcode']:
        barcode = SodaBarcodeScanner("/dev/barcode");

    if args['--simulate-p115m']:
        mdb = P115Master(mdb_dev);
        def billReturned(bill):
            print ("Bill ", bill, " was returned.")
        mdb.returnBill = billReturned

    sys.argv=[sys.argv[0]]
    shell = HWShell()
    shell.cmdloop()
except Exception(e):
    print (e)
    raise e
finally:
    if args['--simulate-soda-barcode']:
        barcode.cleanup();
    if args['--simulate-p115m']:
        mdb.cleanup();
