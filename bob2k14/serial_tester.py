#!/usr/bin/env python3

"""serial_tester, the Soda Machine serial interface tester.

This script is used to test the soda machine serial interfaces.

Usage:
 serial_tester.py mdb <command> [--port=<soda-port>] [(-v|--verbose)]
  serial_tester.py (-h | --help)
  serial_tester.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --port=<soda-port>   	    MDB serial port. [default: /dev/ttyUSB0]
  -v --verbose      	    Verbose debug output.
"""

from docopt import docopt
import subprocess
import serial
import io

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

def mdb_command(port, command):
    port.write(command + "\r")
    port.readline()
    return port.readline()

if __name__ == '__main__':
    arguments = docopt(__doc__, version=get_git_revision_hash())

    if arguments['--verbose']:
        print("Launched with arguments:")
        print(arguments)

    if arguments['--verbose']:
        print("Opening serial port: " + arguments["--port"])

    sodaport = serial.Serial(arguments["--port"], 9600, 8, "N", 1, 3)
    sodawrapper = io.TextIOWrapper(io.BufferedRWPair(sodaport,sodaport,1), encoding='ascii', errors=None, newline=None)
    if arguments['--verbose']:
        print("Command:" + arguments["<command>"])

    print(mdb_command(sodawrapper, arguments["<command>"]))

