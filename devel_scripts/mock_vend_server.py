#!/usr/bin/env python

"""mock_vend_server, server listening for rpc commands, and based on them imitating vending machine events.

In a development environment this server is invoked by vdb_server.py

Usage:
  mock_vend_server.py  [--port=<port>] [(-v|--verbose)] 
  mock_vend_server.py (-h | --help)
  mock_vend_server.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --port=<port>              Port on which the devel server listens. [default: 8085]
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
import sys

app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

def mvs_RPCThread(app, args):
    app.run(port=int(args['--port']), debug=False, threaded=True)

@jsonrpc.method('mvs.request_auth')
def mvs_request_auth(item):
    debug("MVS: Request auth on {0}".format(item))
    sys.stdout.write('CLINK: REQUEST AUTH ' + str(item) + '\n')
    sys.stdout.flush()
    resp = sys.stdin.readline()
    return resp

@jsonrpc.method('mvs.vend_ok')
def mvs_vend_ok():
    debug("MVS: Vend ok")
    sys.stdout.write('CLINK: VEND OK\n')
    sys.stdout.flush()
    return ""

@jsonrpc.method('mvs.vend_fail')
def mvs_vend_ok():
    debug("MVS: Vend fail")
    sys.stdout.write('CLINK: VEND FAIL\n')
    sys.stdout.flush()
    return "" 

def mvs_shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def mvs_shutdown():
    mvs_shutdown_server()
    debug("Server shutdown request finished")
    return 'Server shutting down...'

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

if __name__ == '__main__':
    args = docopt(__doc__, version=get_git_revision_hash())

    if args['--verbose']:
        debug(args)

    # Starting RPC Service
    debug("Starting up rpc service on port {0}".format(args['--port']))
    rpcThr = Thread(target = mvs_RPCThread, args = [app, args])
    rpcThr.start()

    try:
      while (1):
        time.sleep(3)
    except KeyboardInterrupt: pass

    debug("Shutting down rpc service")
    requests.post('http://127.0.0.1:{0}/shutdown'.format(args['--port']))
