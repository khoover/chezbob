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
from flask import Flask, Response, jsonify
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

app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)
b_master = None

def ds_RPCThread(app, args):
    print ("Starting devel rpc service")
    app.run(port=int(args['--port']), debug=False, threaded=True)
    print ("Devel rpc service finished")

@jsonrpc.method('ds.barcode_scan')
def ds_barcode_scan(barcode):
    print ("Got request to scan {0}".format(barcode))
    global b_master
    os.write(b_master, struct.pack('B', 0))
    os.write(b_master, bytes(barcode, "ascii"))
    os.write(b_master, b'\x0d')

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

if __name__ == '__main__':
    args = docopt(__doc__, version=get_git_revision_hash())

    if args['--verbose']:
        print("Launched with args:")
        print(args)

    soda_port = args['--soda-port']
    b_master, b_slave = pty.openpty()

    # Bring up Soda
    debug("Starting up soda_serve on port {0} with db {1}".format(\
      soda_port, args['--db-file']))
    sodaProc = subprocess.Popen([BASEDIR + 'bob2k14/soda_serve.py', 'serve',\
      'sqlite:///' + args['--db-file'], '--port', soda_port])
    debug("soda_serve.py running as process {0}".format(sodaProc.pid))

    # Bring up barcode_server
    debug("Starting up barcode_serve on pipe {0}".format(os.ttyname(b_slave)))
    barcodeProc = subprocess.Popen([BASEDIR + 'bob2k14/barcode_server.py', \
      'scan-barcode', '--barcode-port', os.ttyname(b_slave),
      '--endpoint', "http://127.0.0.1:{0}/api".format(soda_port), '--verbose'])
    debug("barcode_server.py running as process {0}".format(barcodeProc.pid))

    # Starting RPC Service
    debug("Starting up rpc service on port {0}".format(args['--port']))
    rpcThr = Thread(target = ds_RPCThread, args = [app, args])
    rpcThr.start()

    try:
      while (1):
        time.sleep(3)
    except KeyboardInterrupt: pass

    debug("Shutting down rpc service")
    requests.post('http://127.0.0.1:{0}/shutdown'.format(args['--port']))

    debug("Shutting down barcode_server")
    barcodeProc.terminate()
    barcodeProc.wait()
    debug("Shutting down soda_serve")
    sodaProc.terminate()
    sodaProc.wait()
