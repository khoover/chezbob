#!/usr/bin/python
#
# Generate a random UPC barcode number.
#
# This is a random 12-digit number, with two constraints:
#   - The first digit is "4" which puts it in the privately-allocated space of
#     barcodes.
#   - The last digit is the check digit.
#
# See http://en.wikipedia.org/wiki/Universal_Product_Code for details.

import random

digits = [4] + [random.randrange(10) for _ in range(10)]

checksum = 0
for i in range(len(digits)):
    if i % 2 == 0:
        checksum += digits[i] * 3
    else:
        checksum += digits[i] * 1

digits.append(-checksum % 10)

print ''.join(map(str, digits))
