#!/usr/bin/env python3

import sys

with open('floor_locations.txt') as f:
    lines = list(f)

locs = {}

for line in lines[2:-2]:
    item,loc = line.split('|')
    item = item.strip()
    loc = loc.strip()
    locs[item] = loc

with open(sys.argv[1]) as f:
    lines = list(f)

def lockey(line):
    item = line[5:-1]
    return locs[item]

lastloc = ''
for line in sorted(lines, key=lockey):
    if lockey(line) != lastloc:
        lastloc = lockey(line)
        print()
    print(line, end='')
