#!/usr/bin/env python3

"""serial_tester, the Soda Machine serial interface tester.

This script is used to test the soda machine serial interfaces.

Usage:
  serial_tester.py mdb <command> [--port=<soda-port>] [(-v|--verbose)]
  serial_tester.py scan-barcode [--barcode-port=<port>] [(-v|--verbose)]
  serial_tester.py (-h | --help)
  serial_tester.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --port=<soda-port>   	    MDB serial port. [default: /dev/ttyUSB0]
  --barcode-port=<port>     Barcode serial port. [default: /dev/ttyUSB1]
  -v --verbose      	    Verbose debug output.
"""

from docopt import docopt
import subprocess
import serial
import io
import struct
import binascii
import functools

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
                      print(code)
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
        elif arguments["mdb"]:
             if arguments['--verbose']:
                  print("Opening serial port: " + arguments["--port"])
             sodaport = serial.Serial(arguments["--port"], 9600, 8, "N", 1, 3)
             sodawrapper = io.TextIOWrapper(io.BufferedRWPair(sodaport,sodaport,1), encoding='ascii', errors=None, newline=None)
             if arguments['--verbose']:
                 print("Command:" + arguments["<command>"])
             print(mdb_command(sodawrapper, arguments["<command>"]))
             sodawrapper.close()
             sodaport.close()
    except KeyboardInterrupt:
         if barcodeport != None:
              barcodeport.close()
