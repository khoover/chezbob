#!/usr/bin/env python

"""scan_barcode.py, simulate a barcode being scanned

This script launches all the neccessary servers for bob (soda_serve, vdb_server, mdb_server, barcode_server) or their mock equivalents. It monitors all of them, and shuts them down when the session is done (Ctrl+C)

Usage:
  scan_barcode.py [--barcode-port=port] [(-v|--verbose)] <num>
  scan_barcode.py (-h | --help)
  scan_barcode.py --version

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
      "params": [ args['<num>']  ],
      "jsonrpc": "2.0",
      "id": 0
    }

    if args['--verbose']:
      print("Sending: " + data)


    requests.post("http://127.0.0.1:{0}/api".format(args['--barcode-port']), \
      data=json.dumps(payload),\
      headers={'content-type': 'application/json'}).json()
