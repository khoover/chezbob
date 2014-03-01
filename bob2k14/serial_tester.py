#!/usr/bin/env python3

"""serial_tester, the Soda Machine serial interface tester.

Usage:
  serial_tester.py test --soda-port=<soda-port> [(-v|--verbose)]
  serial_tester.py (-h | --help)
  serial_tester.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --soda-port=<soda-port>   Soda machine serial port. [default: /dev/ttyUSB0]
  -v --verbose      Verbose debug output.
"""

from docopt import docopt
import subprocess
import serial

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD']))

def mdb_command(port, command):
    port.write(command + "\r")
    port.readline()
    return port.readline(None, '\r')

if __name__ == '__main__':
    arguments = docopt(__doc__, version=get_git_revision_hash())

    if arguments['-v']:
        print(arguments)

    if arguments['-v']:
        print("Opening serial port: " + arguments["--soda-port"])

    sodaport = serial.Serial(arguments["--soda-port"], 9600, 8, "N", 1, 3)
    print(mdb_command(sodaport, "T2"))

