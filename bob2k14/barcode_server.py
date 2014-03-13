#!/usr/bin/env python3.4

"""barcode_server, the Soda Machine serial barcode server.

This script listens for barcodes being scanned and sends them to the JSONrpc endpoint.

Usage:
  barcode_server.py scan-barcode [--barcode-port=<port>] [(-v|--verbose)]
  barcode_server.py (-h | --help)
  barcode_server.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --barcode-port=<port>     Barcode serial port. [default: /dev/ttyUSB1]
  --endpoint=<port>         JSON RPC endpoint. [default: http://soda.ucsd.edu:8080/api]
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

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

def mdb_command(port, command):
    port.write(command + "\r")
    port.readline()
    return port.readline()

if __name__ == '__main__':
    arguments = docopt(__doc__, version=get_git_revision_hash())
    try:
        if arguments['--verbose']:
             print("Launched with arguments:")
             print(arguments)
    
        if arguments["scan-barcode"]:
            barcodeport = serial.Serial(arguments["--barcode-port"], 9600, 8, "N", 1)
            while True:
                  length = struct.unpack('B', barcodeport.read())[0]
                  if arguments['--verbose']:
                      print("Length: " + str(length))
                  if length == 0:
                      #Raw ASCII
                      code = ""
                      curcode = b'\x0d'
                      for i in iter(functools.partial(barcodeport.read,1), b'\x0d'):
                           code += i.decode('ascii')
                      #print(code)
                      #here's where we do the jsonrpc.
                      payload = {
                          "method": "soda.remotebarcode",
                          "params": [ code[0], code[1:]],
                          "jsonrpc": "2.0",
                           "id": 0
                      }
                      requests.post(arguments['--endpoint'], data=json.dumps(payload), headers={'content-type': 'application/json'}).json()
                  else:
                      opcode = barcodeport.read()
                      if arguments['--verbose']:
                           print("Opcode:" + str(binascii.hexlify(opcode), 'ascii'))
                      data = barcodeport.read(length - 2)
                      if arguments['--verbose']:
                           print("Data:" + str(binascii.hexlify(data), 'ascii'))
                      checksum = barcodeport.read(2)		
                      if arguments['--verbose']:
                           print("Checksum:" + str(binascii.hexlify(checksum), 'ascii'))
                      if opcode == b'\xf3':
                           print(data[3:].decode('ascii'))
    except KeyboardInterrupt:
         if barcodeport != None:
              barcodeport.close()
