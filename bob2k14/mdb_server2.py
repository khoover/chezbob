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
  --mdb-port=<port>         MDB serial port. [default: /dev/ttyUSB0]
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
    return ""

readcommand = types.SimpleNamespace()
readcommand.event = Event()
readcommand.data = ""
readcommand.command = ""
def mdb_command(port, command):
    readcommand.event.clear()
    port.write(command + "\r")
    return readcommand.data.rstrip("\r\n")

def send_remote(data):
    #here's where we do the jsonrpc.
    payload = {
                "method": "Soda.remotemdb",
                "params": [ data ],
                "jsonrpc": "2.0",
                "id": 0
              }
    print("Sending: "  + data)
    requests.post(arguments['--remote-endpoint'], data=json.dumps(payload), headers={'content-type': 'application/json'}).json()
    print("Sent: " + data)
    return ""

def mdb_thread(arguments):
    #1 second timeout.
    mdbport = io.open(arguments["--mdb-port"], 'rt', errors='ignore')
    data = ""
    tempdata = ""
    pendingCommand = False
    try:
         while True:
         # attempt to read data off the mdb port. if there is, send it to the mdb endpoint
              try:
                   if not pendingCommand:
                        data += mdbport.readline()
                   if '\n' in data:
                        send_remote(data)
                        data = ""
              except Exception as e:
                   print(e)
    except Exception as e:
         print ("Exception in mdbthread:" + e)
         if mdbport != None:
              mdbport.close()

def rpc_thread(arguments):
     mdbport = io.open(arguments["--mdb-port"], 'wt', buffering=1, errors='ignore')
     try:
         print("Resetting coin changer...")
         mdbport.write('R1\r') #Reset the changer
         mdbport.write('N FFFF\r') #Enable coin acceptance
         mdbport.write('E1\r') #Enable coin acceptance
         time.sleep(1)
         print("Resetting bill validator...")
         mdbport.write('R2\r') #Reset bill validator
         time.sleep(1)
         mdbport.write('P2\r') #Poll for reset OK
         mdbport.write('L FFFF\r') #Accept all bills
         mdbport.write('V 0000\r') #Security off
         mdbport.write('J FFFF\r') #Escrow
         mdbport.write('E2\r') #Enable bill acceptance
         while True:
               request = requestqueue.get()
               if (arguments['--verbose']):
                     print("Command: " + request.command)
               request.result = mdb_command(mdbport, request.command)
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

    # init in case everything is not yet
    mdb = Thread(target = mdb_thread, args = [arguments])
    mdb.start()
    rpc = Thread(target = rpc_thread, args = [arguments])
    rpc.start()
    app.run(host=arguments['--address'], port=int(arguments['--port']), debug=False,threaded=True)
