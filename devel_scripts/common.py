import sys;

def debug(msg):
  sys.stderr.write(msg + '\n')

def error(msg):
  debug(msg)
  sys.exit(-1)
