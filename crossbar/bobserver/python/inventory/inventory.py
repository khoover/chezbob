import datetime
import decimal

from twisted.internet.defer import inlineCallbacks
from twisted.logger import Logger

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession
#from autobahn.wamp.exception import ApplicationError

import psycopg2
import psycopg2.extras

DB_CREDS = {"dbname": "bob", "user": "bob", "host": "localhost"}

NODE_NAME = 'inventory_srv'
PREFIX = "chezbob.inventory."

log = Logger()


def preserialize(obj):
    obj = dict(obj)
    for key, val in obj.items():
        if type(val) == datetime.datetime:
            obj[key] = val.isoformat()
            log.warn("Converting: {} to {}".format(val, obj[key]))
        elif type(val) == datetime.date:
            obj[key] = val.isoformat()
            log.warn("Converting: {} to {}".format(val, obj[key]))
        elif type(val) == decimal.Decimal:
            obj[key] = float(val)
            log.warn("Converting: {} to {}".format(val, obj[key]))
        elif type(val) == dict:
            obj[key] = preserialize(val)
    return obj


class InvalidOperandException(Exception):
    pass


class InventoryManager(object):
    def __init__(self, session):
        self._conn = psycopg2.connect(**DB_CREDS)
        self._conn.set_client_encoding("utf-8")

        # Initialize protected set with useless value to keep postgres happy
        # when you don't protect anything.
        self._protected = {-1}

        self._session = session

    def _announce(self, bulkid, value):
        log.info("Publishing update: {}/{}".format(bulkid, value))
        self._session.publish(PREFIX + 'update', (bulkid, value))

    def _announce_reset(self):
        log.info("Publishing reset!")
        self._session.publish(PREFIX + 'reset', [])

    def _get_cursor(self):
        return self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def _get_current_inventory(self, bulkid):
        query = ("SELECT units FROM inventory"
                 " WHERE date::date = current_date AND bulkid = %s")
        cursor = self._get_cursor()
        cursor.execute(query, [bulkid])

        if not cursor.rowcount:
            return None

        row = cursor.fetchone()
        return row['units']

    def _insert_if_needed(self, bulkid):
        query = ("INSERT INTO inventory"
                 " (date, bulkid, units, cases, loose_units, case_size)"
                 " ( SELECT now(), bulkid, 0, 0, 0, quantity"
                 "   FROM bulk_items"
                 "   WHERE bulkid = %s )")

        if self._get_current_inventory(bulkid) is not None:
            return

        cursor = self._get_cursor()
        cursor.execute(query, [bulkid])

    def _add_to_db(self, bulkid, amount):
        query = ("UPDATE inventory"
                 " SET"
                 "  date = now(),"
                 "  units = greatest(0, units + %s),"
                 "  cases = greatest(((units + %s) / case_size), 0),"
                 "  loose_units = greatest(((units + %s) %% case_size), 0)"
                 " WHERE date::date = current_date AND bulkid = %s"
                 " RETURNING *")
        cursor = self._get_cursor()
        cursor.execute(query, [amount, amount, amount, bulkid])
        return cursor.fetchone() if cursor.rowcount else None

    def add_to_inventory(self, bulkid, amount):
        """ Adds 'amount' to the inventory count for 'bulkid'.
            - Increments inventory count for bulkid by amount given
            - Amount can be negative or positive
            - The stored inventory value, however, will be non-negative
            - Returns new amount and publishes to update channel
            - Returns -1 on flagged bulkids
        """
        if type(bulkid) != int:
            raise InvalidOperandException("{} is not a bulkid".format(bulkid))

        # Protected bulkids don't get updates
        if bulkid in self._protected:
            return -1

        # I'm lazy, so let's just insert a nice zero-inventory to add on to.
        self._insert_if_needed(bulkid)

        # Update the value
        result = self._add_to_db(bulkid, amount)

        # Commit it!
        self._conn.commit()

        # This might fail, but if it does, we're in trouble
        units = result['units']

        # Publish it to the world
        self._announce(bulkid, units)

        # Return the new value for completeness
        return units

    def remove_from_inventory(self, bulkid):
        """Removes the bulkid from today's inventory."""
        if type(bulkid) != int:
            raise InvalidOperandException("{} is not a bulkid".format(bulkid))

        # Protected bulkids don't get updates
        if bulkid in self._protected:
            return -1

        query = """"
        DELETE FROM inventory WHERE date::date = current_date AND bulkid = %s
        """
        cursor = self._get_cursor()
        cursor.execute(query, [bulkid])

        # Commit it!
        self._conn.commit()

        # Publish it to the world
        self._announce(bulkid, None)

    def get_inventory_value(self, bulkid):
        """Retrieves current inventory value for 'bulkid'.
            - Returns current value for that bulkid
            - Returns -1 on flagged bulkids
        """
        if type(bulkid) != int:
            raise InvalidOperandException("{} is not a bulkid".format(bulkid))

        # Protected bulkids don't get updates
        if bulkid in self._protected:
            return -1

        previous = self._get_current_inventory(bulkid)
        return previous
        #return 0 if previous is None else previous

    def get_uninventoried(self):
        """Retrieves list of items that haven't been inventoried or disabled.

        Returns list of objects/dicts with names and bulkids.
        """
        return []

        query = """
            SELECT bulkid, description
            FROM bulk_items
            WHERE
                active
                AND bulkid NOT IN (
                    SELECT bulkid
                    FROM inventory
                    WHERE
                        date::date = current_date
                        AND units != 0)
                AND bulkid NOT IN %s
        """
        """
        cursor = self._get_cursor()
        cursor.execute(query, [tuple(self._protected)])
        return [
            dict(x) for x in cursor.fetchall()] if cursor.rowcount else None
            """

    def flag_for_no_update(self, bulkid):
        """ Flags 'bulkid' for *NOT* adding to the inventory.
            - Subsequent attempts to get_inventory_value will return -1
            - Publishes to update channel with value of -1
        """

        if type(bulkid) != int:
            raise InvalidOperandException("{} is not a bulkid".format(bulkid))

        self._protected.add(bulkid)

        # Publish it to the world
        self._announce(bulkid, -1)

    def unflag_for_no_update(self, bulkid):
        """Removes 'bulkid' from flagged list
            - All previous updates to this bulkid are lost
        """

        if type(bulkid) != int:
            raise InvalidOperandException("{} is not a bulkid".format(bulkid))

        self._protected.discard(bulkid)

        # Publish it to the world
        self._announce(bulkid, 0)

    def zero_unprotected(self):
        """Sets zero inventory for all uninventoried, unprotected bulkids.

        All active bulkids not in inventory or specifically protected will have
        value set to zero.
        """

        blanks_query = ("INSERT INTO inventory"
                        " (date, bulkid, units, loose_units, cases, case_size)"
                        " ( SELECT now(), bulkid, 0, 0, 0, quantity"
                        "   FROM bulk_items"
                        "   WHERE active"
                        "       AND bulkid NOT IN %s"
                        "       AND bulkid NOT IN ("
                        "           SELECT bulkid FROM inventory"
                        "           WHERE date >= current_date))")

        cursor = self._get_cursor()

        try:
            # Add zero inventories to everything that we didn't take inventory
            # on, or specifically mark to ignore, provided that the item is
            # active.
            log.info("Setting zeros on inventory")
            protected_tuple = tuple(self._protected)
            cursor.execute(blanks_query, [protected_tuple])
            self._conn.commit()

        except psycopg2.IntegrityError:
            log.error("Rolling back due to integrity error.")
            self._conn.rollback()
            raise

        self._session.publish(PREFIX + 'set_zeros', [])
        self.reset(False)

    def reset(self, announce):
        """Resets the inventory state to empty.
            - Everything disabled is un-disabled.
            - Everything inventoried is removed.
        """
        self._protected = {-1}
        if announce:
            self._announce_reset()

    def _fetchone(self, query, *args, **kwargs):
        cursor = self._get_cursor()
        cursor.execute(query, *args, **kwargs)
        return cursor.fetchone() if cursor.rowcount else None

    def _get_bulkitem_from_barcode(self, bc):
        query = """
        SELECT *, 'bulkitem' as \"type\" FROM bulk_items WHERE bulkbarcode = %s
        """
        return self._fetchone(query, [bc])

    def _get_bulkitem_from_bulkid(self, bulkid):
        query = """
        SELECT *, 'bulkitem' as \"type\" FROM bulk_items WHERE bulkid = %s
        """
        return self._fetchone(query, [bulkid])

    def _get_product_from_barcode(self, bc):
        query = """
        SELECT *, 'product' as \"type\" FROM products WHERE barcode = %s
        """
        return self._fetchone(query, [bc])

    def get_barcode_details(self, bc):
        result = self._get_product_from_barcode(bc)
        if result:
            if result['bulkid']:
                result = dict(result)
                result['bulkitem'] = dict(self._get_bulkitem_from_bulkid(
                    result['bulkid']))
                result['bulkitem'] = (dict(result['bulkitem'])
                                      if result['bulkitem'] else None)
        else:
            result = self._get_bulkitem_from_barcode(bc)

        if not result:
            log.error("Couldn't find result for invalid barcode: {}".format(bc))
            if bc.startswith("0") and len(bc) == 13:
                log.error("Retrying barcode check with EAN->UPCA: {}".format(bc))
                return self.get_barcode_details(bc[1:])
            if bc.startswith("0") and len(bc) == 8:
                log.error("Retrying barcode check with shorter UPC-E: {}".format(bc))
                return self.get_barcode_details(bc[1:-1])

            result = {"type": "unknown"}

        return preserialize(result)


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
        log.info("Starting inventory...")

        self.inventory = InventoryManager(self)
        self._register_functions(self.inventory)

        for x in self.heartbeat():
            yield x

