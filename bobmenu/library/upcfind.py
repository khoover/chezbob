#!/usr/bin/python

# upcfind.py: Figure out a table of UPC and ISBN prefixes
# This program is in the public domain.

# Written by Andrew Plotkin (erkyrath@eblong.com)
# http://www.eblong.com/zarf/bookscan/

import sys
import string
import fileinput
import re

def mangle(line):
    line = string.strip(line)
    if (len(line) == 0):
        return None
    if (line[0] == '#'):
        return None
    commentpos = string.find(line, "#")
    if (commentpos >= 0):
        line = line[0:commentpos]
        line = string.strip(line)
    return line

upcmap = {}
curline = None

def add_mapping(upc, isbn):
    if (len(upc) == 5):
        upc = "0"+upc;
    if (len(upc) != 6):
        print "UPC prefix", upc, "should be five or six digits"
        return
    if (len(isbn) == 0):
        print "ISBN prefix cannot be empty"
        return
    if (upcmap.has_key(upc)):
        if (upcmap[upc] == isbn):
            return
        if (curline == None):
            print "<upc-map>: ",
        else:
            print "line", curline, ":",
        print "UPC prefix", upc, "is already in the list",
        print "as", upcmap[upc], "-- not", isbn
        return
    upcmap[upc] = isbn

try:
    for line in fileinput.input('upc-map'):
        line = string.strip(line)
        if (len(line) == 0 or line[0] == "#"):
            continue
        eqpos = string.find(line, "=")
        if (eqpos >= 0):
            upcval = line[0:eqpos]
            isbnval = line[eqpos+1:]
            add_mapping(upcval, isbnval)
except:
    pass

upcnull = "------------ -----"
isbnnull = "============= ====="

lastupc = upcnull
lastisbn = isbnnull
curline = 0;

for line in fileinput.input():
    curline = curline+1
    line = mangle(line)
    if (line == None):
        continue
    eqpos = string.find(line, "=")
    if (eqpos >= 0):
        upcval = line[0:eqpos]
        isbnval = line[eqpos+1:]
        add_mapping(upcval, isbnval)
        continue
    if (len(line) == 18 and line[12] == " "):
        lastupc = line
    if (len(line) == 19 and line[13] == " "):
        lastisbn = line[:13]
    if (len(line) == 13):
        lastisbn = line
    if (lastupc[13:18] == lastisbn[7:12]):
        #print "###4:", lastupc[0:6], lastisbn[3:7]
        add_mapping(lastupc[0:6], lastisbn[3:7])
        lastupc = upcnull
        lastisbn = isbnnull
    if (lastupc[14:18] == lastisbn[8:12]):
        #print "###5:", lastupc[0:6], lastisbn[3:8]
        add_mapping(lastupc[0:6], lastisbn[3:8])
        lastupc = upcnull
        lastisbn = isbnnull
    if (lastupc[15:18] == lastisbn[9:12]):
        #print "###6:", lastupc[0:6], lastisbn[3:9]
        add_mapping(lastupc[0:6], lastisbn[3:9])
        lastupc = upcnull
        lastisbn = isbnnull

file = open('upc-map', 'w')
file.write("# UPC Prefix -- ISBN Prefix mapping file\n")
keys = upcmap.keys()
keys.sort()
for upc in keys:
    isbn = upcmap[upc]
    file.write(upc + "=" + isbn + "\n")
file.close()
