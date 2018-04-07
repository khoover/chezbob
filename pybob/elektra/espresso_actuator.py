"""The process responsible for activating the espresso grinder."""

import argparse

import RPi.GPIO as GPIO
import six
import txaio

from autobahn.wamp.exception import ApplicationError
from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks


PIN_MODE = GPIO.BCM  # Or GPIO.BOARD
#"digout_pins": [13, 19, 5, 6],
DEFAULT_ACTUATOR_PIN = 13

PREFIX = u'chezbob.espresso.grinder'

DEFAULT_ROUTER = u'wss://chezbob.ucsd.edu:8095/ws'
DEFAULT_REALM = u'chezbob'


class EspressoActuator(ApplicationSession):

    @inlineCallbacks
    def onJoin(self, details):
        self.log.info("EspressoActuator connected: {details}", details=details)

        # init GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(PIN_MODE)

        self._actuator_pin = self.config.extra['args'].output_pin

        # setup GPIO pin
        GPIO.setup(self._actuator_pin, GPIO.OUT)

        # Initialize low
        GPIO.output(self._actuator_pin, GPIO.LOW)

        # setup pin state vectors
        self._digout_state = False

        # register methods on this object for remote calling via WAMP
        uri = u'{}.actuate_for'.format(PREFIX)
        yield self.register(self.actuate_for, uri)

        self.log.info("EspressoActuator registered procedure {}".format(uri))

        # signal we are done with initializing our component
        self.publish(u'{}.on_ready'.format(PREFIX))

        self.log.info("EspressoActuator ready.")

    def onLeave(self, details):
        self.log.info("Session closed: {details}", details=details)
        GPIO.cleanup()
        self.disconnect()

    def onDisconnect(self):
        self.log.info("Connection closed")

    def _set_output(self, state):
        if type(state) != bool:
            raise ApplicationError(
                "ApplicationError.INVALID_ARGUMENT", "state must be a bool")

        # only process if state acually changes
        if self._digout_state == state:
            return False

        # now set the digout value
        GPIO.output(self._actuator_pin,
                    GPIO.HIGH if state else GPIO.LOW)
        self._digout_state = state

        if state:
            self.log.info("Grinder activated")
        else:
            self.log.info("Grinder deactivated")

        return True

    def actuate_for(self, period=10):
        """
        Trigger a digout.
        """
        if type(period) != int and type(period) != float and period > 0:
            raise ApplicationError(
                "ApplicationError.INVALID_ARGUMENT",
                "period must be a positive number")

        if self._digout_state is True:
            raise ApplicationError(
                "ApplicationError.INVALID_ARGUMENT",
                "already actuating")

        self._set_output(True)

        # publish WAMP event
        self.publish(u'{}.activated'.format(PREFIX))

        outerself = self

        class Countdown(object):
            def __init__(self, remaining):
                self.remaining = remaining
                self()

            def __call__(self):
                if int(self.remaining) != self.remaining:
                    offset = self.remaining - int(self.remaining)
                    self.remaining = int(self.remaining)
                    reactor.callLater(offset, self)
                elif self.remaining > 0:
                    outerself.log.info("{}s remaining".format(self.remaining))
                    outerself.publish(
                        u'{}.remaining'.format(PREFIX),
                        remaining=self.remaining)
                    self.remaining -= 1
                    reactor.callLater(1, self)
                else:
                    outerself.log.info(
                        "Clearing output".format(self.remaining))
                    outerself.publish(
                        u'{}.deactivated'.format(PREFIX))
                    outerself._set_output(False)

        Countdown(period)


if __name__ == '__main__':
    # parse command line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--debug',
                        action='store_true', help='Enable debug output.')
    parser.add_argument("--router", type=six.text_type,
                        default=DEFAULT_ROUTER, help='WAMP router URL.')
    parser.add_argument("--realm", type=six.text_type,
                        default=DEFAULT_REALM, help='WAMP router realm.')
    parser.add_argument("--output_pin", type=int,
                        default=DEFAULT_ACTUATOR_PIN, help='PIN to actuate')

    args = parser.parse_args()

    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    extra = {"args": args}

    # create and start app runner for our app component ..
    runner = ApplicationRunner(url=args.router, realm=args.realm, extra=extra)
    runner.run(EspressoActuator, auto_reconnect=True)

