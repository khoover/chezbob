#!/usr/bin/env python3.4

"""vdb_server, the Soda Machine vdb server.

This script listens for events on vdb and writes it to and endpoint and also listens for incoming (unsolicited vdb commands).

Usage:
  vdb_server.py serve [--vdb-port=<port>] [--remote-endpoint=<ep>] [--address=<listen-address>] [--port=<port>]  [(-v|--verbose)]
  vdb_server.py (-h | --help)
  vdb_server.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --vdb-port=<port>         vdb serial port. [default: /dev/ttyS0]
  --remote-endpoint=<ep>    JSON RPC endpoint. [default: http://127.0.0.1:8080/api]
  --address=<ep>            Address to listen on. [default: 0.0.0.0]
  --port=<port>             Port to listen on. [default: 8083]
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

app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

requestqueue = queue.Queue()

@jsonrpc.method('Vdb.command')
def vdb_command_json(command):
    request = types.SimpleNamespace()
    request.event = Event()
    request.command = command
    print("Remote command: " + command)
    requestqueue.put(request)
    return ""

readcommand = types.SimpleNamespace()
readcommand.event = Event()
readcommand.data = ""
readcommand.command = ""
def vdb_command(port, command):
    readcommand.event.clear()
    port.write(command + "\r")
    return readcommand.data.rstrip("\r\n")

def send_remote(data):
    #here's where we do the jsonrpc.
    payload = {
                "method": "Soda.remotevdb",
                "params": [ data ],
                "jsonrpc": "2.0",
                "id": 0
              }
    print("Sending: " + data)
    requests.post(arguments['--remote-endpoint'], data=json.dumps(payload), headers={'content-type': 'application/json'}).json()
    return ""

def handle_local(data):
    if (data == "F"):
        print("CLINK: DISABLE CARD READER")
        request = types.SimpleNamespace()
        request.event = Event()
        request.command = "X"
        requestqueue.put(request)
        return True
    elif (data == "H"):
        print("CLINK: VMC SESSION END")
        request = types.SimpleNamespace()
        request.event = Event()
        request.command = "X"
        requestqueue.put(request)
        return True
    elif (data == "M"):
        print("CLINK: POLL/MONITOR")
        request = types.SimpleNamespace()
        request.event = Event()
        request.command = "C"
        requestqueue.put(request)
        return True
    elif (data.startswith("R")):
        print("CLINK: REQUEST")
        request = types.SimpleNamespace()
        request.event = Event()
        request.command = "A"
        requestqueue.put(request)
        return True
    return False
def vdb_thread(arguments):
    #1 second timeout.
    vdbport = io.open(arguments["--vdb-port"], 'rt', errors='ignore')
    data = ""
    tempdata = ""
    pendingCommand = False
    try:
         while True:
         # attempt to read data off the vdb port. if there is, send it to the vdb endpoint
              try:
                   if not pendingCommand:
                        data += vdbport.readline()
                   if '\n' in data:
                        if not handle_local(data.rstrip('\n')):
                            send_remote(data)
                        data = ""
              except Exception as e:
                   print(e)
    except Exception as e:
         print ("Exception in vdbthread:" + e)
         if vdbport != None:
              vdbport.close()

def rpc_thread(arguments):
     vdbport = io.open(arguments["--vdb-port"], 'wt', buffering=1, errors='ignore')
     try:
          while True:
               request = requestqueue.get()
               if (arguments['--verbose']):
                     print("Command: " + request.command)
               request.result = vdb_command(vdbport, request.command)
               if (arguments['--verbose']):
                     print("Result: " + request.result)
               request.event.set()
     except Exception as e:
          print ("Exception in rpcthread: " + str(e))

if __name__ == '__main__':
    arguments = docopt(__doc__, version=get_git_revision_hash())

    if arguments['--verbose']:
        print("Launched with arguments:")
        print(arguments)
    vdb = Thread(target = vdb_thread, args = [arguments])
    vdb.start()
    rpc = Thread(target = rpc_thread, args = [arguments])
    rpc.start()
    app.run(host=arguments['--address'], port=int(arguments['--port']), debug=False,threaded=True)
