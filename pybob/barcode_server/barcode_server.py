#!/usr/local/bin/python3.4
"""TODO: Change me!"""

from __future__ import print_function

import argparse
#import json

try:
    from queue import Queue
except ImportError:
    from Queue import Queue
import sys

from threaded_barcode_scanner import ThreadedBarcodeScanner
from hid_scanner import HIDBarcodeScanner
from serial_scanner import SerialBarcodeScanner

from bob_send import BobApi

# Bullshit nfcpy only handles python 2 - :-P
if (sys.version_info < (3, 0)):
    from nfc_scanner import NFCScanner

DEFAULT_CONFIG_FILE = "/etc/chezbob.json"

def get_args():
    parser = argparse.ArgumentParser()
    #parser.add_argument('-c', '--config_file', type=argparse.FileType(),
    #                    default=file(DEFAULT_CONFIG_FILE),
    #                    help="Configuration file to use.")
    parser.add_argument('--type', type=int, default=0,
                        help="Client type (0 == normal, 1 == soda)")
    parser.add_argument('--id', type=int,
                        help="Client ID")
    parser.add_argument('-i', '--hid_device', action='append',
                        help="HID device to open")
    parser.add_argument('-s', '--serial_device', action='append',
                        help="Serial device to open")

    if (sys.version_info < (3, 0)):
        parser.add_argument('-n', '--nfc_device', action='append',
                            help="NFC device to open")

    #parser.add_argument('-b', '--background', action="store_true",
    #                    help="Run in background (requires -o)")
    return parser.parse_args(), parser


def get_list_with_precedence(items, merge=False):
    results = []
    for x in items:
        if not isinstance(x, list):
            x = [x]
        if merge:
            results.extend(x)
        else:
            return x
    return results


def get_enqueuer(q):
    def enqueue_barcode(_, barcode):
        q.put(barcode)
    return enqueue_barcode

def get_running_scanner(scanner, cb):
    tscanner = ThreadedBarcodeScanner(scanner)
    tscanner.start()
    tscanner.get_barcode(callback=cb)
    return tscanner

def main():
    args, _ = get_args()

    #config = json.load(args.config_file)

    q = Queue()
    enqueuer = get_enqueuer(q)

    scanners = []
    if args.serial_device:
        for name in args.serial_device:
            sscanner = SerialBarcodeScanner(name)
            scanners.append(get_running_scanner(sscanner, enqueuer))

    if args.hid_device:
        for name in args.hid_device:
            iscanner = HIDBarcodeScanner(name)
            scanners.append(get_running_scanner(iscanner, enqueuer))

    if (sys.version_info < (3, 0)):
        if args.nfc_device:
            for name in args.nfc_device:
                nscanner = NFCScanner(name)
                scanners.append(get_running_scanner(nscanner, enqueuer))

    endpoint = "http://127.0.0.1:8080/api"
    api = BobApi(endpoint, args.type, args.id)

    while True:
        item = q.get()
        print(item)
        api.send_barcode(item)

    #if args.serial_device:
    #    parser.error("Serial interfaces not yet implemented")

    #sodad_endpoint = config['sodad']['endpoint']
    #hid_device = get_list_with_precedence(
    #    [args.input_device, config['barcoded']['hid_device']]
    #)

    #print(config)

if __name__ == "__main__":
    sys.exit(main())

