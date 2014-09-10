#!/usr/bin/env python

"""barcode.py, simulate a barcode being scanned

This script simulates a barcode being scanned on the soda machine scanner.

Usage:
  barcode.py scan [--barcode-port=port] [(-v|--verbose)] <barcode>
  barcode.py scan-product [--barcode-port=port] [(-v|--verbose)] <product-name>
  barcode.py login [--barcode-port=port] [(-v|--verbose)] <username>
  barcode.py list-products
  barcode.py (-h | --help)
  barcode.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --barcode-port=<port>     Port where watchdog server is listening [default: 8084]
  -v --verbose      	      Verbose debug output.
  barcode                   barcode to send
  list-products             List all products and corresponding barcodes
  list-products             List all users and corresponding barcodes of their id
  username                  username to scan 
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
from common import BASEDIR, debug, error
import pty
import sys
import os
from struct import pack

sys.path.append(BASEDIR + 'bob2k14')
os.environ['CB_DEVEL'] = '1'

from models import app, products, userbarcodes, users
def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

if __name__ == '__main__':
    args = docopt(__doc__, version=get_git_revision_hash())

    # Will need DB access. Set it up
    if args['list-products'] or args['login'] or args['scan-product']:
      app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + BASEDIR + 'deploy/app.db'

    if args['--verbose']:
        print("Launched with args:")
        print(args)

    if args['list-products']:
      for p in products.query.all():
        print(p.name + ' ' + p.barcode)
    elif args['scan-product']:
      product_name = args['<product-name>']
      products = products.query.filter(products.name.like('%' + product_name + '%')).all()

      if (len(products) == 0):
        error("No products found matching " + product_name)

      if (len(products) > 1):
      
        err_str = str(len(products)) + ' entries found. Which one do you want:'
        for p in products:
          err_str += '\n' + p.name + ' ' + p.barcode

        error(err_str + '\n')

      payload = {
        "method": "ds.barcode_scan",
        "params": [ 'A' + products[0].barcode ],
        "jsonrpc": "2.0",
        "id": 0
      }

      if args['--verbose']:
        print("Sending: " + data)

      requests.post("http://127.0.0.1:{0}/api".format(args['--barcode-port']), \
        data=json.dumps(payload),\
        headers={'content-type': 'application/json'}).json()
    elif args['login']:
      username = args['<username>']
      user = users.query.filter(users.username == username).first()

      if (not user):
        error("Unknown user " + username) 

      barcode = userbarcodes.query.filter(userbarcodes.userid == user.userid).first()

      if (not barcode):
        error("User " + username + " doesn't have an associated barcode") 
        
      payload = {
        "method": "ds.barcode_scan",
        "params": [ 'A' + barcode.barcode ],
        "jsonrpc": "2.0",
        "id": 0
      }

      if args['--verbose']:
        print("Sending: " + data)

      requests.post("http://127.0.0.1:{0}/api".format(args['--barcode-port']), \
        data=json.dumps(payload),\
        headers={'content-type': 'application/json'}).json()
    elif args['scan']:
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
