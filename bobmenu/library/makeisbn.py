#!/usr/bin/python

# makeisbn.py: Turn UPC and EAN barcodes into ISBNs
# This program is in the public domain.

# Written by Andrew Plotkin (erkyrath@eblong.com)
# http://www.eblong.com/zarf/bookscan/

import sys
import string
import fileinput
import re

isbndigits = re.compile("^[0-9Xx]+")
bardigits = re.compile("^[0-9 ]+")
justdigits = re.compile("^[0-9]+")

def matchesall(reg, str):
    res = reg.search(str)
    if (res == None):
        return 0
    if (len(res.group()) == len(str)):
        return 1
    return 0

def mangle(line):
    line = string.strip(line)
    if (len(line) == 0):
        return (None, None)
    if (line[0] == '#'):
        return (None, line)
    commentpos = string.find(line, '#')
    if (commentpos < 0):
        comment = None
    else:
        comment = ' ' + line[commentpos:]
        line = string.strip(line[0:commentpos])
    return (line, comment)

def isbnchecksum(line):
    if (len(line) == 10):
        line = line[0:9]
    if (len(line) != 9):
        return '# ISBN should be 9 digits, excluding checksum!'
    sum = 0
    count = 0
    for ix in line:
        sum = sum + (10 - count) * string.atoi(ix)
        count = count + 1
    sum = sum % 11
    if (sum != 0):
        sum = 11 - sum
    if (sum == 10):
        line = line + 'X'
    else:
        line = line + string.digits[sum]
    return line

def lineout(line, extra, comment, last = [None]):
    if (line == None):
        line = ''
    if (not(line != '' and extra == None and line == last[0])):
        if (extra == None):
            sys.stdout.write(line + comment + '\n')
        else:
            sys.stdout.write('# ' + line + ' : ' + extra + comment + '\n')
    if (line != '' and extra == None):
        last[0] = line

upcmap = {}

try:
    for line in fileinput.input('upc-map'):
        line = string.strip(line)
        if (len(line) == 0 or line[0] == "#"):
            continue
        eqpos = string.find(line, "=")
        if (eqpos >= 0):
            upcval = line[0:eqpos]
            isbnval = line[eqpos+1:]
            upcmap[upcval] = isbnval
except:
    sys.stdout.write('# # Could not open upc-map file; have you run upcfind?')

for line in fileinput.input():
    (line, comment) = mangle(line)
    if (comment == None):
        comment = ''
    if (line == None):
        #sys.stdout.write(comment + '\n')
        lineout(None, None, comment)
        continue
    linelen = len(line)
    if (matchesall(isbndigits, line) and linelen == 10):
        #sys.stdout.write(line + comment + '\n')
        lineout(line, None, comment)
        continue
    if (matchesall(bardigits, line) and (linelen == 13 or linelen == 19)):
        if (line[0:3] != '978'):
            #sys.stdout.write('# ' + line + ' : not a 978 EAN' + comment + '\n')
            lineout(line, 'not a 978 EAN', comment)
            continue
        line = isbnchecksum(line[3:12])
        #sys.stdout.write(line + comment + '\n')
        lineout(line, None, comment)
        continue
    if (matchesall(bardigits, line) and linelen == 12):
        #sys.stdout.write('# ' + line + 
        #   ' : UPC barcode requires five-digit extension' + comment + '\n')
        lineout(line, 'UPC barcode requires five-digit extension', comment)
        continue
    if (matchesall(bardigits, line) and linelen == 18):
        prefix = line[0:6]
        suffix = line[13:18]
        if (not upcmap.has_key(prefix)):
            #sys.stdout.write('# ' + line + ' : Unknown UPC prefix '
            #   + prefix + comment + '\n')
            lineout(line, ('Unknown UPC prefix ' + prefix), comment)
            continue
        ipref = upcmap[prefix]
        line = ipref + suffix[(len(ipref)-4) : ]
        line = isbnchecksum(line)
        #sys.stdout.write(line + comment + '\n')
        lineout(line, None, comment)
        continue
    if (string.find(line, "=") >= 0):
        #sys.stdout.write('# ' + line + comment + '\n')
        continue
    #sys.stdout.write('# ' + line + ' : unrecognized format' + comment + '\n')
    lineout(line, 'Unrecognized format', comment)
