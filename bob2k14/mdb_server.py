#!/usr/bin/env python3.4

"""mdb_server, the Soda Machine mdb server.

This script listens for events on mdb and writes it to and endpoint and also listens for incoming (unsolicited mdb commands).

Usage:
  mdb_server.py serve [--mdb-port=<port>] [--remote-endpoint=<ep>] [--address=<listen-address>] [--port=<port>]  [(-v|--verbose)]
  mdb_server.py (-h | --help)
  mdb_server.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --mdb-port=<port>         MDB serial port. [default: /dev/ttyACM0]
  --remote-endpoint=<ep>    JSON RPC endpoint. [default: http://127.0.0.1:8080/api]
  --address=<ep>            Address to listen on. [default: 0.0.0.0]
  --port=<port>             Port to listen on. [default: 8081]
  -v --verbose      	    Verbose debug output.
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

app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

requestqueue = queue.Queue()

@jsonrpc.method('Mdb.command')
def mdb_command_json(command):
    request = types.SimpleNamespace()
    request.event = Event()
    request.command = command
    requestqueue.put(request)
    request.event.wait()
    return request.result

def mdb_command(port, command):
    port.write((command + "\r"))
    time.sleep(0.1)
    port.readline()
    time.sleep(3)
    return port.readline().rstrip('\r\n')

def send_remote(data):
    #here's where we do the jsonrpc.
    payload = {
                "method": "Soda.remotemdb",
                "params": [ data ],
                "jsonrpc": "2.0",
                "id": 0
              }
    requests.post(arguments['--remote-endpoint'], data=json.dumps(payload), headers={'content-type': 'application/json'}).json()
    return ""

def mdb_thread(arguments):
    mdbport = None
    while True:
        try:
            if os.path.exists(arguments["--mdb-port"]):
                mdbport = io.open(arguments["--mdb-port"], 'rt', buffering=8)
            else:
                mdbport = io.open("/dev/ttyACM1", 'rt', buffering=8)
            try:
                 while True:
                 # attempt to read data off the mdb port. if there is, send it to the mdb endpoint
                       data = mdbport.readline().rstrip('\r\n')
                       if len(data) != 0:
                            if arguments['--verbose']:
                                print(data)
                            if data[0:8] == "S2 10 03":
                                #vending command
                                if arguments['--verbose']:
                                      print("Sent: " + data[9:])
                                send_remote( data[9:])
            except Exception as e:
                 print ("Exception in mdbthread" + str(e))
        except Exception as e:
             print ("Exception in mdbthread" + str(e))

def rpc_thread(arguments):
        mdbport = None
        while True:
            try:
                if os.path.exists(arguments["--mdb-port"]):
                    mdbport = io.open(arguments["--mdb-port"], 'wt')
                else:
                    mdbport = io.open("/dev/ttyACM1", 'wt')
                while True:
                      try:
                           request = requestqueue.get_nowait()
                           if arguments['--verbose']:
                                print("Command: " + request.command)
                           mdbport.write((request.command + '\r\n'))
                           request.result = ""
                           #request.result = mdb_command(mdbwrapper, request.command)
                           if arguments['--verbose']:
                                print("Result: " + request.result)
                           request.event.set()
                      except queue.Empty as e:
                           pass
            except Exception as e:
                print ("Exception in rpcthread:" + str(e))
if __name__ == '__main__':
    arguments = docopt(__doc__, version=get_git_revision_hash())

    if arguments['--verbose']:
        print("Launched with arguments:")
        print(arguments)


    mdb = Thread(target = mdb_thread, args = [arguments])
    mdb.start()
    rpc = Thread(target = rpc_thread, args = [arguments])
    rpc.start()
    app.run(host=arguments['--address'], port=int(arguments['--port']), debug=arguments['--verbose'],threaded=True)
