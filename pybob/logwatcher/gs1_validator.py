"""Barcode validation."""

import math

# http://www.gs1.org/how-calculate-check-digit-manually


def validate_gtin13(bc):
    check = 0
    for posn, digit in enumerate(bc[:-1]):
        digit = int(digit)
        mult = 3 if posn % 2 else 1
        #print(digit, mult, posn)
        check += mult * digit
    check = math.ceil(check / 10.0) * 10 - check
    return check == int(bc[-1])


def validate(bc):
    if len(bc) < 12:
        return True

    if len(bc) == 12:
        bc = "0" + bc
    return validate_gtin13(bc)

