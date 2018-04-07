#!/usr/local/bin/python3.4
"""TODO: Change me!"""

from __future__ import print_function

import argparse
import six

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
from twisted.internet.error import ReactorNotRunning

from autobahn import wamp
from autobahn.wamp.exception import ApplicationError
from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.twisted.choosereactor import install_reactor

import txaio

import sys

class SubscriptionPrinter(ApplicationSession):
    """
    Logs anything it's subscribed to. For testing.
    """

    def print_message(self, args):
        print(args)

    #@inlineCallbacks
    def onJoin(self, details):
        print("OnJoin called")

        args = self.config.extra['args']

        for channel in args.CHANNEL:
            self.subscribe(self.print_message, channel)

        self.log.info("Printer ready.")

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--router", type=str,
                        default=u"wss://chezbob.ucsd.edu:8095/ws",
                        help='Router URL.')
    parser.add_argument("--realm", type=str, default=u"chezbob",
                        help='Router realm.')
    parser.add_argument("--debug", action='store_true',
                        help='Print debugging messages')

    parser.add_argument("CHANNEL", type=six.text_type, nargs="+",
                        help='Name for this barcode reader')

    return parser.parse_args(), parser



def main():
    args, _ = get_args()

    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    # create and start app runner for our app component ..
    extra = {"args": args}
    runner = ApplicationRunner(url=args.router, realm=args.realm, extra=extra)
    runner.run(SubscriptionPrinter, auto_reconnect=True)

if __name__ == "__main__":
    sys.exit(main())
