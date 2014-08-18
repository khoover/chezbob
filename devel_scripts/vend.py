#!/usr/bin/env python

"""vend.py, simulate vending events.

This scripts allows simulating both low-level vending events (request-auth,
vend-ok, vend-fail), as well as higher-level combinations of those
(buy-successful = request-auth, A, vend-ok; buy-failed=request-auth, A,
vend-fail; buy-denied=request-auth, D;).


Usage:
  vend.py request-auth [--mvs-port=port] [(-v|--verbose)] <str>
  vend.py vend-ok [--mvs-port=port] [(-v|--verbose)] 
  vend.py vend-fail [--mvs-port=port] [(-v|--verbose)] 
  vend.py buy-successful [--mvs-port=port] [(-v|--verbose)] <str>
  vend.py buy-failed [--mvs-port=port] [(-v|--verbose)] <str>
  vend.py buy-denied [--mvs-port=port] [(-v|--verbose)] <str>
  vend.py choices 
  vend.py (-h | --help)
  vend.py --version

Options:
  request-auth              Simulate a request-auth event. Takes one parameter - which button was pressed. For valid options run 'vend.py choices'
  vend-ok                   Simulate a vend-ok event
  vend-fail                 Simulate a vend-fail event
  buy-successful            Simulate a successful purchase. Equivalent to a request-auth event followed by a vend-ok event
  buy-failed                Simulate a failed purchase. Equivalent to a request-auth event followed by a vend-fail event
  buy-denied                Simulate a vending machine press, and expect a denied response.
  choices                   Print the possible choices for request-auth (and buy-successful, buy-failed)

  -h --help                 Show this screen.
  --version                 Show version.
  --mvs-port=<port>         Port where watchdog server is listening [default: 8085]
  -v --verbose      	      Verbose debug output.
  barcode                   barcode to send
"""


from common import BASEDIR, debug, error
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
import pty
from struct import pack

args = None

def post(payload):
    global args
    if args['--verbose']:
      print("Sending: " + payload)

    resp = requests.post("http://127.0.0.1:{0}/api".format(args['--mvs-port']), \
      data=json.dumps(payload),\
      headers={'content-type': 'application/json'}).json()
    return resp

def req_auth(item):
    payload = {
      "method": "mvs.request_auth",
      "params": [ item ],
      "jsonrpc": "2.0",
      "id": 0
    }

    config = json.load(open(BASEDIR + 'bob2k14/config.json'))
    if (item not in config['sodamapping']):
      error("Invalid vending machine item {0}. Must be one of: {1}".format(item, \
        config['sodamapping'].keys()))

    return post(payload)

def vend_ok():
    payload = {
      "method": "mvs.vend_ok",
      "params": [ ],
      "jsonrpc": "2.0",
      "id": 0
    }

    return post(payload) 

def vend_fail():
    payload = {
      "method": "mvs.vend_fail",
      "params": [ ],
      "jsonrpc": "2.0",
      "id": 0
    }

    return post(payload) 

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

if __name__ == '__main__':
    args = docopt(__doc__, version=get_git_revision_hash())

    if args['--verbose']:
        print("Launched with args:")
        print(args)

    if args['request-auth']:
      resp = req_auth(args['<str>'])
      print(resp)
    elif args['vend-ok']:
      resp = vend_ok()
      print(resp)
    elif args['vend-fail']:
      resp = vend_fail()
      print(resp)
    elif args['buy-successful']:
      resp = req_auth(args['<str>'])
      if (resp['result'] != 'A\n'):
        error("Purchase not authorized!")
      resp = vend_ok()
      if resp['result'] != '':
        error("Unexpected result for vend-ok: {0}".format(resp))
    elif args['buy-failed']:
      resp = req_auth(args['<str>'])
      if (resp['result'] != 'A\n'):
        error("Purchase not authorized!")
      resp = vend_fail()
      if resp['result'] != '':
        error("Unexpected result for vend-failed: {0}".format(resp))
    elif args['buy-denied']:
      resp = req_auth(args['<str>'])
      if (resp['result'] != 'D\n'):
        error("Purchase got authorized!")
    elif args['choices']:
      config = json.load(open(BASEDIR + 'bob2k14/config.json'))
      for item in config['sodamapping']:
        print(item)


