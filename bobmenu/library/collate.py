#!/usr/bin/python

# collate.py: Merge and sort tab-separated data files
# This program is in the public domain.

# Written by Andrew Plotkin (erkyrath@eblong.com)
# http://www.eblong.com/zarf/bookscan/

import sys
import string
import fileinput

def casesort(s1, s2):
    s1 = string.lower(s1)
    s2 = string.lower(s2)
    if (s1 < s2):
        return -1
    if (s1 > s2):
        return 1
    return 0


list = []

for filename in sys.argv[1:]:
    for line in fileinput.input(filename):
        line = string.rstrip(line)
        if (len(line) == 0):
            continue
        if (line[0] == '#'):
            sys.stderr.write('Skipping comment: ' + line + '\n')
            continue
        if (string.find(line, '\t') < 0):
            sys.stderr.write('No tab in line: ' + line + '\n')
            continue
        list.append(line)

list.sort(casesort)

sys.stdout.write('Author\tTitle\n')
for line in list:
    sys.stdout.write(line)
    sys.stdout.write('\n')

