from bitstruct import pack
from serial import SerialDevice

# Soda Barcode Scanner:
# The barcode scanner appears as a serial port on which
# we enter barcodes 1 at a time as follows;
#   1) Null-byte
#   2) barcode in ASCII
#   3) Terminating byte - \0xd
class SodaBarcodeScanner(SerialDevice):
    def scan(self, barcode):
        self.write(pack('u8', 0))
        self.write(bytes(barcode, "ascii"))
        self.write(b'\x0d')
