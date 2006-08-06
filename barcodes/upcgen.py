#!/usr/bin/python

"""Extremely simple program to generate UPC barcode images.

Expects a list of barcodes to be specified on the command-line, and creates an
image for each one.  Only encodes standard 12-digit UPC-A barcodes
(EAN.UCC-12), not any other variants.  Expects the checksum digit to be
included as part of the provided barcode, and does not perform any checks that
the checksum digit is correct.

Doesn't produce any fancy barcode formatting either, just a single solid block
of bars.

Based on the article at <http://en.wikipedia.org/wiki/Universal_Product_Code>.
"""

__author__ = "Michael Vrable <mvrable@cs.ucsd.edu>"

import sys
import Image

# Binary encodings of digits in UPC barcodes.  These are the L encodings, used
# for the left half of the barcode; the R encodings used in the right half are
# the one's complement of these codes.
upc_codes = {
    '0': "0001101",
    '1': "0011001",
    '2': "0010011",
    '3': "0111101",
    '4': "0100011",
    '5': "0110001",
    '6': "0101111",
    '7': "0111011",
    '8': "0110111",
    '9': "0001011",
}
start_code = "101"
guard_code = "01010"

def upc_encode_digit(digit, form='L'):
    """Return the encoded form of a single UPC digit.

    'form' is optional and should be either "L" (default) or "R", depending
    upon whether the left- or right-handed side encoding is desired.
    """

    result = upc_codes[digit]
    if form == 'R':
        result = "".join([{'0': '1', '1': '0'}[c] for c in result])
    return result

def upc_to_bits(digits):
    """Convert a string of digits to the sequence of bits which represent it."""

    if len(digits) != 12:
        raise ValueError("Invalid barcode length (expected 12 digits)")

    digits_l = list(digits[0:6])
    digits_r = list(digits[6:12])

    barcode = start_code
    for d in digits_l:
        barcode += upc_encode_digit(d, 'L')
    barcode += guard_code
    for d in digits_r:
        barcode += upc_encode_digit(d, 'R')
    barcode += start_code

    return barcode

def bits_to_image(bits, height=40):
    rawbits = "".join([{'0': '\377', '1': '\0'}[c] for c in bits])
    im = Image.fromstring('L', (len(bits), 1), rawbits)
    return im.resize((len(bits), height)).convert('1')

if __name__ == '__main__':
    for b in sys.argv[1:]:
        image = bits_to_image(upc_to_bits(b))
        image.save(b + ".png")
