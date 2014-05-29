#!/usr/bin/env python3.4

"""vdb_server, the Soda Machine vdb server.

This script listens for events on vdb and writes it to and endpoint and also listens for incoming (unsolicited vdb commands).

Usage:
  vdb_server.py serve [--serverpath=<path>] [--remote-endpoint=<ep>] [--address=<listen-address>] [--port=<port>]  [(-v|--verbose)]
  vdb_server.py (-h | --help)
  vdb_server.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --remote-endpoint=<ep>    JSON RPC endpoint. [default: http://127.0.0.1:8080/api]
  --address=<ep>            Address to listen on. [default: 0.0.0.0]
  --port=<port>             Port to listen on. [default: 8083]
  --serverpath=<path>       Path to process [default: /home/mwei/sodaserv/sodaserv]
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
import sarge
from flask import Flask, Response, jsonify
from flask_jsonrpc import JSONRPC
import queue
from threading import Thread
from threading import Event
import sys
from collections import namedtuple
import types
import time
from sarge import Feeder, Capture, Command
from io import TextIOWrapper

app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)
proc = None
def get_git_revision_hash():
    pass
#    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))
message_types = ["CLINK: REQUEST AUTH", "CLINK: VEND FAIL", "CLINK: VEND OK"]

requestqueue = queue.Queue()

@jsonrpc.method('Vdb.command')
def vdb_command_json(command):
    global proc
    print("Remote command: " + command)
    proc.stdin.write((command + '\n').encode('utf-8'))
    proc.stdin.flush()
    return ""

def send_remote(data):
    #here's where we do the jsonrpc.
    payload = {
                "method": "Soda.remotevdb",
                "params": [ data ],
                "jsonrpc": "2.0",
                "id": 0
              }
    print("Sending: " + data)
    try:
        requests.post(arguments['--remote-endpoint'], data=json.dumps(payload), headers={'content-type': 'application/json'}).json()
    except:
        pass
    return ""

def vdb_thread(arguments):
    global proc
    proc = Command(arguments['--serverpath'], stdout=Capture(buffer_size=1))
    proc.run(input=subprocess.PIPE, async=True)
    last_poll = None
    while True:
        nextline = proc.stdout.readline().decode('utf-8').rstrip()
        for message in message_types:
            if message in nextline:
                send_remote(nextline)
                break
        if last_poll is None or time.time() > last_poll + 3:
            print("I am polling!")
            last_poll = time.time()
            if proc.poll() != None:
                break

    print("Exited.")
    proc.stdout.close()

if __name__ == '__main__':
    arguments = docopt(__doc__, version=get_git_revision_hash())

    if arguments['--verbose']:
        print("Launched with arguments:")
        print(arguments)
    vdb = Thread(target = vdb_thread, args = [arguments])
    vdb.start()
    app.run(host=arguments['--address'], port=int(arguments['--port']), debug=False,threaded=True)
