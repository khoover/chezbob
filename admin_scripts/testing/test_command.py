#!/usr/bin/python

import os
import sys

if len(sys.argv) == 3:
    print sys.argv[1]
    print sys.argv[2]
    print 'SUCCESS'
else:
    print len(sys.argv)
    print 'FAILURE'
