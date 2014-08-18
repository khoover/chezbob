#!/usr/bin/env python

"""bills.py, simulate events on the money reader

Simulate events sent to the money reader. Due to the asynchronous nature of some responses (esp. coin returns), this does not immediately display the result of the action. (e.g. was the bill accepted or returned). For now you can find this information in the devel_server logs.

Usage:
  bills.py put-bill [--ds-ep=<ep>] [(-v|--verbose)] <amount>
  bills.py put-coin [--ds-ep=<ep>] [(-v|--verbose)] <amount>
  bills.py valid-bills
  bills.py valid-coins
  bills.py (-h | --help)
  bills.py --version

Options:
  put-bill                  Trying simulating a bill being put in. A list of valid bills can be found by running 'bills.py valid-bills'
  put-coin                  Trying simulating a coin being put in. A list of valid coins can be found by running 'bills.py valid-coins'
  valid-bill                Print out valid bill values
  --ds-ep=<ep>              End point for development sever [default: http://127.0.0.1:8084/api]
  -h --help                 Show this screen.
  --version                 Show version.
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
from devel_server import mdb_bill_to_type, mdb_coin_to_type

args = None

def post(payload):
    global args
    if args['--verbose']:
      print("Sending: " + payload)

    resp = requests.post(args['--ds-ep'],\
      data=json.dumps(payload),\
      headers={'content-type': 'application/json'}).json()
    return resp

def put_bill(bill):
    payload = {
      "method": "ds.put_bill",
      "params": [ bill ],
      "jsonrpc": "2.0",
      "id": 0
    }

    if (bill not in mdb_bill_to_type):
      error("Invalid bill value {0}. Must be one of: {1}".format(bill, \
        mdb_bill_to_type.keys()))

    return post(payload)

def put_coin(coin):
    payload = {
      "method": "ds.put_coin",
      "params": [ coin ],
      "jsonrpc": "2.0",
      "id": 0
    }

    if (coin not in mdb_coin_to_type):
      error("Invalid coin value {0}. Must be one of: {1}".format(coin, \
        mdb_coin_to_type.keys()))

    return post(payload)

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

if __name__ == '__main__':
    args = docopt(__doc__, version=get_git_revision_hash())

    if args['--verbose']:
        print("Launched with args:")
        print(args)

    if args['put-bill']:
      resp = put_bill(int(args['<amount>']))
      print(resp)
    if args['put-coin']:
      resp = put_coin(float(args['<amount>']))
      print(resp)
    elif args['valid-bills']:
      bills = list(mdb_bill_to_type.keys())
      bills.sort()
      for bill in bills:
        print(bill)
    elif args['valid-coins']:
      coins = list(mdb_coin_to_type.keys())
      coins.sort()
      for coin in coins:
        print(coin)
