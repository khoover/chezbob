#!/usr/bin/env python3

"""serial_tester, the Soda Machine serial interface tester.

Usage:
  serial_tester.py test [(-v|--verbose)]
  serial_tester.py (-h | --help)
  serial_tester.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  -v --verbose      Verbose debug output.
"""

from docopt import docopt
import subprocess

def get_git_revision_hash():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'])

if __name__ == '__main__':
    arguments = docopt(__doc__, version=get_git_revision_hash())

    if arguments['-v']:
        print(arguments)

