"""Tails sodad's logs and looks for otherwise-unreported errors and events."""

import argparse
import json
import logging
import os
import psycopg2.extensions
import re
import sys

from collections import defaultdict

BOB_PATH = os.environ.get('CHEZ_BOB_PATH', '/git')
sys.path.insert(0, os.path.join(BOB_PATH, 'pybob'))

from private_api import db
from bobslack import private_slack

import gs1_validator
import tail

DEFAULT_OUTPUT_FILE = "/var/log/chezbob/cb_logwatcher.log"

LOG_FILE = "/var/log/chezbob/cb_sodad.log"
CONFIG_FILE = "/etc/chezbob.json"

UNKNOWN_BARCODE_PATTERN = re.compile("Unknown barcode (\d+),")
UNKNOWN_BARCODE_MESSAGE = "UPC-like barcode scanned twice: {bc}"

UNKNOWN_USER_PATTERN = re.compile("Couldn't find user ([a-zA-Z][a-zA-Z0-9]+)")
UNKNOWN_USER_MESSAGE = "Unknown user attempted login: {user}"

DISABLED_USER_PATTERN = re.compile("Disabled user ([a-zA-Z0-9]+) attempted")
DISABLED_USER_MESSAGE = "Disabled user attempted login: {user}"

LOG_FORMAT = (
    "%(asctime)s %(levelname)-7s %(name)-8s %(funcName)-15s %(message)s")

SCAN_COUNT_NOTIFICATION_THRESHOLD = 2


logger = logging.getLogger("logwatcher")

bc_counts = defaultdict(lambda: 0)


def get_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def handle_barcode(body, match, _):
    bc = match.group(1)

    # 6, 12, 13 are UPC-like.
    if len(bc) not in {6, 12, 13} or not gs1_validator.validate(bc):
        return

    bc_counts[bc] += 1

    if bc_counts[bc] == SCAN_COUNT_NOTIFICATION_THRESHOLD:
        msg = UNKNOWN_BARCODE_MESSAGE.format(bc=bc)
        private_slack.send_msg(msg, channel="#unknown_barcodes")
        logger.info(msg)


def handle_user(body, match, _):
    user = match.group(1)
    msg = UNKNOWN_USER_MESSAGE.format(user=user)
    private_slack.send_msg(msg, channel="#unknown_users")
    logger.info(msg)


def handle_disabled(body, match, _):
    user = match.group(1)
    msg = DISABLED_USER_MESSAGE.format(user=user)
    private_slack.send_msg(msg, channel="#disabled_users")
    logger.info(msg)


def handle_sodaoos(body, match, conn):
    config = get_config()
    curs = db.get_cursor()

    soda_num = match.group(1)
    bc = config["sodamap"][soda_num]

    curs.execute("SELECT name FROM products WHERE barcode = %s", (bc,))
    row = curs.fetchone()

    msg = "Failed purchase due to OOS soda: {} ({})".format(row['name'], bc)
    private_slack.send_msg(msg, channel="#out_of_stock")
    logger.info(msg)


PATTERNS = [
    (UNKNOWN_BARCODE_PATTERN, handle_barcode),
    (UNKNOWN_USER_PATTERN, handle_user),
    (DISABLED_USER_PATTERN, handle_disabled),
    (re.compile("Vend FAILED, setting (..) stock to OOS"), handle_sodaoos)
]


def process_msg(msg, conn):
    try:
        body = json.loads(msg)
    except ValueError:
        return

    for pattern, handler in PATTERNS:
        match = pattern.match(body['msg'])
        if match:
            handler(body, match, conn)
        match = None


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--logfile', default=DEFAULT_OUTPUT_FILE,
                        help="Log file to write to.")
    return parser.parse_args()


def setup_logging(verbose, logfile=None):
    root_logger = logging.getLogger()
    formatter = logging.Formatter(LOG_FORMAT)
    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(formatter)
    root_logger.addHandler(streamhandler)

    if logfile:
        filehandler = logging.FileHandler(logfile)
        filehandler.setFormatter(formatter)
        root_logger.addHandler(filehandler)

    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)


def main():
    args = get_args()
    setup_logging(False, args.logfile)

    conn = db.get_conn()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    fn = LOG_FILE
    for line in tail.watch(fn):
        process_msg(line, conn)

if __name__ == "__main__":
    sys.exit(main())

