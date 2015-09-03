from struct import pack
from evdev.ecodes import *
from serial import SerialDevice

keycode = {
    '0' : KEY_0,
    '1' : KEY_1,
    '2' : KEY_2,
    '3' : KEY_3,
    '4' : KEY_4,
    '5' : KEY_5,
    '6' : KEY_6,
    '7' : KEY_7,
    '8' : KEY_8,
    '9' : KEY_9,
}

# Handheld Barcode Scanner:
class HandheldBarcodeScanner(SerialDevice):
    def _sendKey(self, k):
        data = pack('qqHHi', 0,0, EV_KEY, k, 0)
        self.write(data)

    @staticmethod
    def isValidBarcode(c):
        return c.isdigit()

    def scan(self, barcode):
        for c in barcode:
            self._sendKey(keycode[c])
        self._sendKey(KEY_ENTER)
