from twisted.internet.defer import inlineCallbacks
from twisted.logger import Logger

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession
#from autobahn.wamp.exception import ApplicationError

import datetime
import decimal

import psycopg2
import psycopg2.extras

DB_CREDS = {"dbname": "bob", "user": "bob", "host": "localhost"}

NODE_NAME = 'accept_order_srv'
PREFIX = "chezbob.accept_order."

log = Logger()


class InvalidOperandException(Exception):
    pass


class OrderAcceptanceException(Exception):
    pass


def clean_name(name):
    return name[:name.find(" (")]


def normalize_barcode(bc):
    if len(bc) == 8 and bc.startswith("0"):
        return bc[1:-1]
    if len(bc) == 13 and bc.startswith("0"):  # Not sure this is a good idea...
        return bc[1:]
    return bc


def mkresult(result, header, details, supplementary=None):
    result = {"result": result, "header": header, "details": details}
    if supplementary:
        result.update(supplementary)
    return result


def fixtypes(row):
    for key in row.keys():
        typ = type(row[key])
        if typ == datetime.date:
            row[key] = str(row[key])
        elif typ == decimal.Decimal:
            row[key] = float(row[key])
    return row


class OrderAcceptanceManager(object):
    def __init__(self, session):
        self._conn = psycopg2.connect(**DB_CREDS)
        self._conn.set_client_encoding("utf-8")

        self._session = session

        self._detail_cache = {}
        self._order_id_cache = {}

    def _get_cursor(self):
        return self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def _get_order_id(self, day=None):
        if not day:
            day = datetime.date.today()

        if day in self._order_id_cache:
            return self._order_id_cache[day]

        query = 'SELECT id FROM orders WHERE date = %s'
        cursor = self._get_cursor()
        cursor.execute(query, [day])
        if cursor.rowcount:
            order_id = cursor.fetchone()[0]
            self._order_id_cache[day] = order_id
            return order_id
        return None

    def _update_db_with_scan(self, order_id, barcode):
        query = ("UPDATE order_items SET n_scanned ="
                 " (CASE WHEN n_scanned IS NULL THEN 1 ELSE n_scanned + 1 END)"
                 " WHERE order_id = %(oid)s AND"
                 " (bulk_type_id ="
                 "      (SELECT bulkid FROM bulk_items"
                 "       WHERE bulkbarcode = %(bc)s)"
                 "  OR"
                 "  bulk_type_id ="
                 "      (SELECT bulkid FROM products WHERE barcode = %(bc)s))"
                 " RETURNING *")
        cursor = self._get_cursor()
        cursor.execute(query, {"oid": order_id, "bc": barcode})
        if cursor.rowcount:
            return fixtypes(dict(cursor.fetchone()))
        return None

    def _update_db_with_bi(self, order_id, bi, offset):
        query = ("UPDATE order_items SET n_scanned ="
                 " (CASE WHEN n_scanned IS NULL"
                 "  THEN %(offset)s ELSE n_scanned + %(offset)s END)"
                 " WHERE order_id = %(oid)s AND bulk_type_id = %(bid)s"
                 " RETURNING *")
        cursor = self._get_cursor()
        cursor.execute(query, {"offset": offset, "oid": order_id, "bid": bi})
        if cursor.rowcount:
            return fixtypes(dict(cursor.fetchone()))
        return None

    def _delete_empty_resolved(self, order_id):
        query = ("DELETE FROM order_items"
                 " WHERE number = 0 AND order_id = %(oid)s")
        cursor = self._get_cursor()
        cursor.execute(query, {"oid": order_id})

    def _resolve_db_with_bi(self, order_id, bi):
        query = ("UPDATE order_items SET number = n_scanned"
                 " WHERE order_id = %(oid)s AND bulk_type_id = %(bid)s"
                 " RETURNING *")
        cursor = self._get_cursor()
        cursor.execute(query, {"oid": order_id, "bid": bi})
        if cursor.rowcount:
            result = fixtypes(dict(cursor.fetchone()))
            if result['number'] == 0:
                self._delete_empty_resolved(order_id)
            return result
        return None

    def get_bi_details(self, bi):
        if bi in self._detail_cache:
            return self._detail_cache[bi]

        query = ("SELECT * FROM bulk_items WHERE bulkid = %s")
        cursor = self._get_cursor()
        cursor.execute(query, [bi])
        result = None
        if cursor.rowcount:
            result = fixtypes(dict(cursor.fetchone()))

        self._detail_cache[bi] = result
        return result

    def _common_update(self, db_fn, order_day, *args, **kwargs):
        # Returns dict with:
        #   result from "success"/"warning"/"error"/"info"
        #   header - SHORT text to display
        #   details - longer description

        order_id = self._get_order_id(order_day)

        if not order_id:
            return mkresult("error", "No Order", "No order is active today.")

        # Update the database
        new_row = db_fn(order_id, *args, **kwargs)
        if not new_row:
            return mkresult("error", "Unexpected",
                            "Unknown item or item not in order.")

        bulk_item = self.get_bi_details(new_row['bulk_type_id'])

        remaining = new_row['number'] - new_row['n_scanned']

        extra = {
            "bulk_item": bulk_item, "remaining": remaining,
            "n_scanned": new_row['n_scanned'], "expected": new_row["number"]}

        total_line = "({} of {}) {}".format(
            new_row['n_scanned'], new_row["number"],
            clean_name(bulk_item['description']))

        if remaining < 0:
            result = mkresult("warning", "EXTRA", total_line, extra)
        else:
            result = mkresult("success", "OK", total_line, extra)

        self._conn.commit()

        # Publish an update to listeners with result
        self._session.publish(PREFIX + 'scan_result', result)

        # Return a result to the caller.
        return result

    def modify(self, bi, value, order_day):
        if value != 1 and value != -1:
            return mkresult("error", "Invalid value",
                            "Small increments or decrements only.")

        if not self.get_bi_details(bi):
            return mkresult("error", "Invalid", "Invalid bulk ID provided")

        return self._common_update(
            self._update_db_with_bi, order_day, bi, value)

    def resolve(self, bi, order_day):
        # TODO - set quantity = n_scanned
        if not self.get_bi_details(bi):
            return mkresult("error", "Invalid", "Invalid bulk ID provided")

        return self._common_update(
            self._resolve_db_with_bi, order_day, bi)

    def scan(self, barcode, scanner, order_day):
        return self._common_update(
            self._update_db_with_scan, order_day, normalize_barcode(barcode))

    def get_unresolved(self, order_day=None):
        """
        """
        log.info("Received request for unresolved")

        if order_day:
            try:
                order_day = datetime.datetime.strptime(
                    order_day, "%Y-%m-%d").date()
            except ValueError:
                return mkresult("error", "Bad Day", "Invalid day format.")
        else:
            order_day = datetime.date.today()

        order_id = self._get_order_id(order_day)
        if not order_id:
            return mkresult(
                "error", "No Order", "No order active on that day.")

        query = (" SELECT"
                 "   number as expected,"
                 "   (case when n_scanned is null"
                 "    then 0 else n_scanned end) as n_scanned,"
                 "   (case when n_scanned is null"
                 "    then number else number - n_scanned end) as remaining,"
                 "   bi.*"
                 " FROM order_items oi"
                 "  LEFT OUTER JOIN bulk_items bi"
                 "  ON bi.bulkid = bulk_type_id"
                 " WHERE order_id = %s"
                 "  AND (case when n_scanned is null"
                 "       then number else number - n_scanned end) != 0")

        cursor = self._get_cursor()
        cursor.execute(query, [order_id])
        if cursor.rowcount:
            return [fixtypes(dict(x)) for x in cursor.fetchall()]

        return []


class AppSession(ApplicationSession):
    counter = 0

    def _register_functions(self, obj):
        names = [x for x in dir(obj) if not x.startswith("_")]
        for name in names:
            f = getattr(obj, name)
            full_name = PREFIX + name
            self.register(f, full_name)
            log.info("procedure {} registered".format(full_name))

    @inlineCallbacks
    def heartbeat(self):
        while True:
            yield self.publish('chezbob.heartbeat', NODE_NAME)
            yield sleep(1)

    @inlineCallbacks
    def onJoin(self, details):
        log.info("Starting order acceptance manager...")

        self.manager = OrderAcceptanceManager(self)
        self._register_functions(self.manager)

        for x in self.heartbeat():
            yield x

