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
    request.event.wait()
    return request.result

def mdb_command(port, command):
    port.write((command + "\r").encode())
    port.read()
    readbuffer = ""
    for i in iter(functools.partial(port.read, 1), b'\0xd'):
         readbuffer += i.decode('ascii')
    return readbuffer

def send_remote(data):
    return ""

def mdb_thread(arguments):
    #1 second timeout.
    mdbport = serial.Serial(arguments["--mdb-port"], 9600, 8, "N", 1, 1)
    mdbbuffer = ""
    try:
         while True:
         # attempt to read data off the mdb port. if there is, send it to the mdb endpoint
              data = mdbport.read()
              if data is not None:
                   if len(data) > 0:
                        if data != b'\x0d':
                             mdbbuffer += data.decode('ascii')
                        else:
                             if arguments['--verbose']:
                                  print(mdbbuffer)
                             send_remote(mdbbuffer)
                             mdbbuffer = ""
              #check for enqueued requests.
              try:
                   request = requestqueue.get_nowait()
                   request.result = mdb_command(mdbport, request.command)
                   if arguments['--verbose']:
                        print(request.result)
                   request.event.set()
              except queue.Empty:
                   pass
    except Exception as e:
         print ("Exception in mdbthread:" + str(e))
         if mdbport != None:
              mdbport.close()

if __name__ == '__main__':
    arguments = docopt(__doc__, version=get_git_revision_hash())

    if arguments['--verbose']:
        print("Launched with arguments:")
        print(arguments)
    mdb = Thread(target = mdb_thread, args = [arguments])
    mdb.start()
    app.run(host=arguments['--address'], port=int(arguments['--port']), debug=arguments['--verbose'],threaded=True)
