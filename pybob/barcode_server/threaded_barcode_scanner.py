"""A wrapper to add asynchronous barcode scanning."""

import logging
import time
import threading
import sys


LOGGER = logging.getLogger(__name__)

WAIT_TIMEOUT = 2

class ScannerNotRunningException(Exception):
    """Thrown when you try to interact with a non-running thread."""
    pass


class ThreadedBarcodeScanner(threading.Thread):
    """Sloppy async wrapper for barcode/etc scanners."""
    daemon = True

    mode = "DISABLED"
    condition = None
    exiting = False  # Flag to indicate that we should exit.
    pending_read = None  # The recently-read, not yet returned, scanned data.
    callback = None
    validator = None

    def __init__(self, scanner, *args, **kwargs):
        super(ThreadedBarcodeScanner, self).__init__(*args, **kwargs)
        self.scanner = scanner
        self.condition = threading.Condition()

    def stop(self):
        """Stop the thread."""
        self.exiting = True

    def async_abort(self):
        """Cancel any future callbacks."""
        self.mode = "DISABLED"

        self.pending_read = None
        self.callback = None

    def sync_abort(self):
        """Abort a synchronous scan (from another thread, obv.)."""
        self.condition.acquire()
        self.mode = "DISABLED"

        self.pending_read = None

        self.condition.notify()
        self.condition.release()

    def _handle_async_read(self, scanner_id, barcode):
        """Handle the asynchronous read case."""

        # Once we've validated, we can just call the callback.
        if (self.validator and
                not self.validator(scanner_id, barcode)):
            if self.scanner.supports_beep():
                self.scanner.bad_beep(scanner_id)
            return

        if self.scanner.supports_beep():
            self.scanner.good_beep(scanner_id)

        self.callback(scanner_id, barcode)

    def _handle_sync_read(self, scanner_id, barcode):
        """Handle the synchronous read case."""

        # Once we've validated, notify the waiting thread.
        if (self.validator and
                not self.validator(scanner_id, barcode)):
            if self.scanner.supports_beep():
                self.scanner.bad_beep(scanner_id)
            return False

        if self.scanner.supports_beep():
            self.scanner.good_beep(scanner_id)

        self.condition.acquire()

        self.pending_read = (scanner_id, barcode)

        self.condition.notify()
        self.condition.release()
        return True

    def run(self):
        """Main thread running function."""
        while not self.exiting:
            result = self.scanner.get_barcode()
            if not result:
                continue
            scanner_id, barcode = result

            if self.mode == "DISABLED":
                if self.scanner.supports_beep():
                    self.scanner.bad_beep(scanner_id)
            elif self.mode == "SYNC":
                if self._handle_sync_read(scanner_id, barcode):
                    self.mode = "DISABLED"
            elif self.mode == "ASYNC":
                self._handle_async_read(scanner_id, barcode)
            else:
                LOGGER.critical("UNKNOWN MODE: %s", self.mode)
                sys.exit(1)

    def simple_beep(self, scanner_id=0):
        """Beep, assuming the wrapped scanner supports it."""
        self.scanner.simple_beep(scanner_id)

    def good_beep(self, scanner_id=0):
        """Good Beep, assuming the wrapped scanner supports it."""
        self.scanner.good_beep(scanner_id)

    def bad_beep(self, scanner_id=0):
        """Angry beep, assuming the wrapped scanner supports it."""
        self.scanner.bad_beep(scanner_id)

    def supports_beep(self):
        """Whether or not the wrapped scanner supports beeping."""
        return self.scanner.supports_beep()

    def get_barcode(self, callback=None, validator=None, start_id=None):
        """Retrieve a barcode.

        scanner_ids are small integers indicated which scanner produced the
        barcode. This scanner_id is local to the Scanner instance, and allows us
        to support multiple scanners on a single receive base (mostly useful for
        the wireless scanners). Most of the time, this value will be 0, and can
        basically always be ignored.

        If supported, the scanner will emit a negative ('angry') beep if
        validator fails, and a single 'happy' beep otherwise.

        Arguments:
            - callback: If provided, get_barcode will return immediately and
              callback(scanner_id, barcode) will be called when a barcode is
              ready.  Otherwise, will synchronously wait for a barcode, and
              return.

            - validator: If provided, a barcode will only be provided if
              validator(scanner_id, barcode) returns true.

            - start_id: If provided, this scanner_id will do a simple beep to
              indicate that it is ready to scan. Ignored for async scans.

        Returns:
            None or (SCANNER_ID, BARCODE)
        """
        if not self.is_alive():
            raise ScannerNotRunningException()

        self.validator = validator
        if callback:
            self.mode = "ASYNC"
            self.callback = callback
        else:
            self.mode = "SYNC"

            if self.scanner.supports_beep() and start_id is not None:
                self.scanner.simple_beep(start_id)

            self.condition.acquire()

            while not self.pending_read:
                self.condition.wait(timeout=WAIT_TIMEOUT)

            scanner_id, barcode_read = self.pending_read
            self.pending_read = None

            self.condition.release()

            return scanner_id, barcode_read


def main():
    """Simple case for testing."""

    def _async_print(receiver_id, scanner_id, barcode):
        """Stupid printing function that needs a docstring to not whine."""
        print(receiver_id, scanner_id, barcode)

    scanner = ThreadedBarcodeScanner(sys.argv[1])
    scanner.start()
    try:
        while scanner.is_alive():
            print(scanner.get_barcode())
        scanner.get_barcode(callback=_async_print)
        time.sleep(5)
    except KeyboardInterrupt:
        pass
    scanner.stop()


if __name__ == "__main__":
    sys.exit(main())

