#!/usr/bin/env python

"""barcode.py, simulate a barcode being scanned

This script simulates a barcode being scanned on the soda machine scanner.

Usage:
  barcode.py scan [--barcode-port=port] [(-v|--verbose)] <barcode>
  barcode.py (-h | --help)
  barcode.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --barcode-port=<port>     Port where watchdog server is listening [default: 8084]
  -v --verbose      	      Verbose debug output.
  barcode                   barcode to send
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
from struct import pack

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

if __name__ == '__main__':
    args = docopt(__doc__, version=get_git_revision_hash())

    if args['--verbose']:
        print("Launched with args:")
        print(args)

    payload = {
      "method": "ds.barcode_scan",
      "params": [ 'A' + args['<barcode>']  ],
      "jsonrpc": "2.0",
      "id": 0
    }

    if args['--verbose']:
      print("Sending: " + data)


    requests.post("http://127.0.0.1:{0}/api".format(args['--barcode-port']), \
      data=json.dumps(payload),\
      headers={'content-type': 'application/json'}).json()
