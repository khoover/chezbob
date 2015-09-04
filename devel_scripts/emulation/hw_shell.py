#!/usr/bin/env python3.4
"""hw_shell, the fake hardware shell

Usage:
  hw_shell.py [--simulate-p115m] [--simulate-p115s] [--simulate-soda-barcode] [--simulate-handheld-barcode] [--p115m-device=<mdb_dev>] [--p115s-device=<vdb_dev>]
  hw_shell.py (-h | --help)
  hw_shell.py --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  --simulate-p115m              Should we simulate p115m 
  --simulate-p115s              Should we simulate p115s
  --simulate-soda-barcode       Should we simulate the soda barcode scanner 
  --simulate-handhelt-barcode   Should we simulate the handheld barcode scanner
  --p115m-device=<mdb_dev>      Path to /dev node corresponding to P115M. [default: /dev/mdb] 
  --p115s-device=<vdb_dev>      Path to /dev node corresponding to P115S. [default: /dev/vdb] 
"""

import sys
import os
import cmd2
from docopt import docopt
from serial import readline, writeln, _setupPair
from p115m import P115Master, P115ReturnCoin, P115TryAgain
from p115s import P115Slave
from soda_barcode import SodaBarcodeScanner
from handheld_barcode import HandheldBarcodeScanner

args = docopt(__doc__, version="WTF")

# Devices
barcode = None
barcodei = None
mdb = None
vdb = None

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

    if args['--simulate-p115s']:
        def do_press_soda_button(self, line):
            try:
                col = int(line.strip())
                assert (0 <= col and col <= 11) # TODO: How many columns are there?
                vdb.request_auth(col)
                print ("Ok")
            except (ValueError, AssertionError):
                print ("'%s' is not a valid column" % line)

        def do_vend_ok(self, line):
            vdb.vend_ok()
            print ("Ok")

        def do_vend_failed(self, line):
            vdb.vend_failed()
            print ("Ok")
            

    if args['--simulate-soda-barcode']:
        def do_soda_scan(self, line):
            barcode.scan(line.strip())
            print ("Ok")

    if args['--simulate-handheld-barcode']:
        def do_handheld_scan(self, line):
            barcode = line.strip()
            if (not barcodei.isValidBarcode(barcode)):
                print ("%s is not a valid barcode." % barcode)
                return 
            barcodei.scan(barcode)
            print ("Ok")

try:
    mdb_dev = args['--p115m-device']
    vdb_dev = args['--p115s-device']

    if args['--simulate-soda-barcode']:
        barcode = SodaBarcodeScanner("/dev/barcode");

    if args['--simulate-handheld-barcode']:
        barcodei = HandheldBarcodeScanner("/dev/barcodei");

    if args['--simulate-p115m']:
        mdb = P115Master(mdb_dev);
        def billReturned(bill):
            print ("Bill ", bill, " was returned.")
        mdb.returnBill = billReturned

    if args['--simulate-p115s']:
        vdb = P115Slave(vdb_dev);
        def authorized(col):    print ("Authorized to vend on %d " % col)
        def denied(col):    print ("Denied to vend on %d " % col)
        vdb.authorized = authorized
        vdb.denied = denied

    sys.argv=[sys.argv[0]]
    shell = HWShell()
    shell.cmdloop()
except Exception as e:
    print (e)
    raise e
finally:
    if args['--simulate-p115s'] and vdb != None:
        vdb.cleanup();
    if args['--simulate-p115m'] and mdb != None:
        mdb.cleanup();
    if args['--simulate-soda-barcode'] and barcode != None:
        barcode.cleanup();
    if args['--simulate-handheld-barcode'] and barcodei != None:
        barcodei.cleanup()
