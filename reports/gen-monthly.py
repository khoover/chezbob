#!/usr/bin/python
#
# Given a daily dump of finance account balances, create a monthly report which
# lists the changes in account values over each month.  This can be used to
# generate graphs such as monthly sales numbers.

import re
import sys

snapshots = []

print "# Chez Bob monthly transaction summary"
for line in sys.stdin:
    if line.startswith("#"):
        sys.stdout.write(line)
        continue

    m = re.match(r"^(\d{4}-\d{2}-\d{2})\t(.*)$", line)
    if not m:
        print "Malformed line:", line
        continue

    date = m.group(1)
    values = [float(x) for x in m.group(2).split()]
    if len(snapshots) == 0 or re.match(r".*-01$", date):
        snapshots.append((date, values))

if date is not None and not re.match(r".*-01$", date):
    snapshots.append((date, values))

for i in range(len(snapshots) - 1):
    date = snapshots[i][0]
    balance1 = snapshots[i][1]
    balance2 = snapshots[i + 1][1]

    # Allow for extra fields to be added as time progresses; treat them as zero
    while len(balance1) < len(balance2):
        balance1.append(0.0)

    delta = map(
        lambda x, y: (y if y else 0) - (x if x else 0), balance1, balance2)
    sys.stdout.write(
        "%s\t%s\n" % (date, "\t".join("%.02f" % x for x in delta)))
