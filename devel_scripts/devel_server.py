#!/usr/bin/env python

"""devel_server, the watch-dog server for bob's development environment

This script launches all the neccessary servers for bob (soda_serve, vdb_server, mdb_server, barcode_server) or their mock equivalents. It monitors all of them, and shuts them down when the session is done (Ctrl+C)

Usage:
  devel_server.py [--soda-port=<port>] [--mdb-port=<port>] [--vdb-port=<port>] [--db-file=<file>] [--address=<ep>] [--port=<port>] [(-v|--verbose)] 
  devel_server.py (-h | --help)
  devel_server.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --port=<port>              Port on which the devel server listens. [default: 8084]
  --soda-port=<port>        Port the UI listens on. [default: 8080]
  --mdb-port=<port>         Port mdb listens on. [default: 8081]
  --vdb-port=<port>         Port mdb listens on. [default: 8083]
  --db-file=<file>          Path to SQLite database file [default: deploy/app.db]
  -v --verbose      	      Verbose debug output.
"""


from docopt import docopt
import subprocess
import serial
import io
import struct
import binascii
import functools
import requests
import json
from flask import Flask, Response, jsonify, request
from flask_jsonrpc import JSONRPC
import queue
from threading import Thread
from threading import Event
from collections import namedtuple
import types
import time
import os
from common import BASEDIR, debug
import pty
from copy import copy

app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)
b_master = None
m_master = None

# Global variables used by the mdb emulator (the various rpc endpoints for mdb
# and the ds_MDBThread
mdb_bill_to_type = { 1: "00", 5: "01", 10: "02", 20: "03", 50: "04", 100: "05" }
mdb_type_to_bill = { v:k for k, v in mdb_bill_to_type.items() }
mdb_coin_to_type = { 0.5: "00", .10: "01", .25: "02" }
mdb_type_to_coin = { v:k for k, v in mdb_coin_to_type.items() }
mdb_cmd_str = "S2 10 03 "
mdb_coins = { k:0 for k in mdb_coin_to_type.values() }
bill_in_escrow = None
done = False

def ds_RPCThread(app, args):
    debug("Starting devel rpc service")
    app.run(port=int(args['--port']), debug=False, threaded=True)
    debug("Devel rpc service finished")

def readline(fd):
    res = ''
    while 1:
      b = os.read(fd, 1)
      c = bytes.decode(b, "ascii") 
      res += c

      if (c == '\n'):
        return res

def ds_MDBThread(fd):
    global done, mdb_cmd_str, bill_in_escrow
    debug("ds_MDBThread: Starting ...")
    while (not done):
      cmd = readline(fd).strip()

      if (cmd.startswith(mdb_cmd_str)):
        debug("ds_MDBThread: Echoed command {0}".format(cmd))
        continue

      if (cmd == "K1"):
        assert (bill_in_escrow != None)
        writeln_tty(m_master, mdb_cmd_str + "Q2 " + bill_in_escrow)
        debug("ds_MDBThread: Accepted bill {0}".format(\
          mdb_type_to_bill[bill_in_escrow]))
        bill_in_escrow = None
      elif (cmd == "K2"):
        assert (bill_in_escrow != None)
        writeln_tty(m_master, mdb_cmd_str + "Q3 " + bill_in_escrow)
        bill_in_escrow = None
        debug("ds_MDBThread: Returned bill {0}".format(\
          mdb_type_to_bill[bill_in_escrow]))
      elif (cmd.startswith("G ")):
        coin_type = cmd[2:4]
        amount = int(cmd[5:7])
        assert coin_type in mdb_coins and mdb_coins[coin_type] >= amount
        mdb_coins[coin_type] -= amount
        debug("ds_MDBThread: Returned {0} coins of value {1}".format(\
          amount,
          mdb_type_to_coin[coin_type]))
      else:
        debug("ds_MDBThread: Unknown command {0}".format(cmd))
    debug("ds_MDBThread: Quitting...")
      

def writestr(fd, s):
  os.write(fd, bytes(s, "ascii"))

# We read a line immediately after,  since the master seems to echo the command
# we just wrote 
def writeln_tty(fd, s):
  os.write(fd, bytes(s + '\n', "ascii"))

@jsonrpc.method('ds.barcode_scan')
def ds_barcode_scan(barcode):
    debug("Got request to scan {0}".format(barcode))
    global b_master
    os.write(b_master, struct.pack('B', 0))
    writestr(b_master, barcode)
    os.write(b_master, b'\x0d')

@jsonrpc.method('ds.put_bill')
def ds_put_bill(amount):
    global bill_in_escrow, mdb_cmd_str
    iamount = int(amount)
    print ("Got request to put a {0} dolla bill y'all.".format(iamount))
    global m_master, mdb_bill_to_type

    if (iamount not in mdb_bill_to_type):
      return "Error: Bad bill type {0}".format(iamount)

    bill_type = mdb_bill_to_type[iamount] 
    bill_in_escrow = bill_type
    writeln_tty(m_master, mdb_cmd_str + 'Q1 ' + bill_type)
    return "Bill {0} in escrow".format(iamount)

@jsonrpc.method('ds.put_coin')
def ds_put_coin(amount):
    global mdb_cmd_str, mdb_coins
    famount = float(amount)
    print ("Got request to put a {0} coin y'all.".format(famount))
    global m_master, mdb_coin_to_type

    if (famount not in mdb_coin_to_type):
      return "Error: Bad bill type {0}".format(famount)

    coin_type = mdb_coin_to_type[famount] 
    mdb_coins[coin_type] += 1
    writeln_tty(m_master, mdb_cmd_str + 'P1 ' + coin_type)
    return "Put a {0} coin.".format(famount)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    debug("Server shutdown request finished")
    return 'Server shutting down...'

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

def extend(d, k, v):
    d1 = copy(d)
    d1[k]=v
    return d1

def startServer(name, port, args, env = None):
  debug("Starting {0} server on {1}".format(name, port))
  if (not env):
    p = subprocess.Popen(args)
  else:
    p = subprocess.Popen(args, env=env)
  debug("{0} server running as process {1}".format(name, p.pid))
  return p

def stopServer(name, proc):
  debug("Shutting down {0}".format(name))
  proc.terminate()
  proc.wait()

if __name__ == '__main__':
    args = docopt(__doc__, version=get_git_revision_hash())

    if args['--verbose']:
        print("Launched with args:")
        print(args)

    soda_port = args['--soda-port']
    soda_ep = "http://127.0.0.1:{0}/api".format(soda_port)
    vdb_port = args['--vdb-port']
    vdb_ep = "http://127.0.0.1:{0}/api".format(vdb_port)
    mdb_port = args['--mdb-port']
    mdb_ep = "http://127.0.0.1:{0}/api".format(mdb_port)

    b_master, b_slave = pty.openpty()
    m_master, m_slave = pty.openpty()

    db_file = os.path.abspath(args['--db-file'])
    # Bring up Soda
    sodaProc = startServer("soda_serve", soda_port, \
      [BASEDIR + 'bob2k14/soda_serve.py', 'serve', 'sqlite:///' + db_file, \
        '--port', soda_port, '--mdb-server-ep', mdb_ep, '--vdb-server-ep', \
        vdb_ep],
      extend(os.environ, 'CB_DEVEL', '1'))

    # Bring up barcode_server
    barcodeTTY = os.ttyname(b_slave)
    barcodeProc = startServer("barcode_server", barcodeTTY, \
      [BASEDIR + 'bob2k14/barcode_server.py', \
      'scan-barcode', '--barcode-port', os.ttyname(b_slave),
      '--endpoint', soda_ep, '--verbose'])

    # Bring up mdb_server
    mdbTTY = os.ttyname(m_slave)
    mdbProc = startServer("mdb_server", mdbTTY, \
      [BASEDIR + 'bob2k14/mdb_server.py', 'serve',\
      '--remote-endpoint', soda_ep, '--port', mdb_port, \
      '--mdb-port', mdbTTY, '--verbose'])

    # Start mdb thread
    mdbThread = Thread(target = ds_MDBThread, args = [ m_master ])
    mdbThread.start()

    # Bring up vending server
    vdbProc = startServer("vdb_serve",  vdb_port, [\
      BASEDIR + 'bob2k14/vdb_server.py', 'serve', \
      '--remote-endpoint', soda_ep, '--port', vdb_port, \
      '--serverpath', BASEDIR + 'devel_scripts/mock_vend_server.py'])

    # Starting RPC Service
    debug("Starting up rpc service on port {0}".format(args['--port']))
    rpcThr = Thread(target = ds_RPCThread, args = [app, args])
    rpcThr.start()

    try:
      while (1):
        time.sleep(3)
    except KeyboardInterrupt: pass

    done = True
    writeln_tty(m_master, "BYE.\n")
    debug("Shutting down rpc service")
    requests.post('http://127.0.0.1:{0}/shutdown'.format(args['--port']))

    stopServer("vdb_server", vdbProc)
    stopServer("mdb_server", mdbProc)
    stopServer("barcode_server", barcodeProc)
    stopServer("soda_serve", sodaProc)
    mdbThread.join()
