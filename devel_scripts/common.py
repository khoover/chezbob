import sys;
import os

BASEDIR=os.path.dirname(os.path.abspath(__file__)) + '/../'

def debug(msg):
  sys.stderr.write(msg + '\n')

def error(msg):
  debug(msg)
  sys.exit(-1)
