from collections import defaultdict

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


class InvalidOperandException(Exception):
    pass


class InventoryManager(object):
    def __init__(self, session):
        self._conn = psycopg2.connect(**DB_CREDS)
        self._conn.set_client_encoding("utf-8")

        self._protected = set()
        self._inventory = defaultdict(lambda: 0)

        self._session = session

    def _announce(self, bulkid, value):
        log.info("Publishing update: {}/{}".format(bulkid, value))
        self._session.publish(PREFIX + 'update', (bulkid, value))

    def _announce_reset(self):
        log.info("Publishing reset!")
        self._session.publish(PREFIX + 'reset', [])

    def _get_cursor(self):
        return self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def add_to_inventory(self, bulkid, amount):
        """ Adds 'amount' to the inventory count for 'bulkid'.
            - Increments inventory count for bulkid by amount given
            - Amount can be negative or positive
            - The stored inventory value, however, must be non-negative
            - Returns new amount and publishes to update channel
            - Returns -1 on flagged bulkids
        """
        if type(bulkid) != int:
            raise InvalidOperandException("{} is not a bulkid".format(bulkid))

        # Protected bulkids don't get updates
        if bulkid in self._protected:
            return -1

        # Update the value
        self._inventory[bulkid] += amount
        if self._inventory[bulkid] < 0:  # Cap it non-negative
            self._inventory[bulkid] = 0

        # Publish it to the world
        self._announce(bulkid, self._inventory[bulkid])

        # Return the new value for completeness
        return self._inventory[bulkid]

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

        # Return the new value for completeness
        return self._inventory[bulkid]

    def flag_for_no_update(self, bulkid):
        """ Flags 'bulkid' for *NOT* adding to the inventory.
            - Subsequent attempts to get_inventory_value will return -1
            - Publishes to update channel with value of -1
        """

        if type(bulkid) != int:
            raise InvalidOperandException("{} is not a bulkid".format(bulkid))

        self._protected.add(bulkid)
        if bulkid in self._inventory:
            del self._inventory[bulkid]

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

    def commit(self, set_zeros):
        """Pushes inventory to database.
            - time chosen is as of call to commit()
            - all active bulkids not in inventory (flagged or counted) will
              have value set to zero if set_zeros is true
            - Implicit zeros do not overwrite existing db entries
            - Entries in local database *do* replace pre-existing inventory for
              that item on this day.
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

        delete_query = ("DELETE FROM inventory"
                        " WHERE date >= current_date AND bulkid = %s")

        valued_query = ("INSERT INTO inventory"
                        " (date, bulkid, units, cases, loose_units, case_size)"
                        " ( SELECT now(), bulkid, %s,"
                        "          (%s / quantity), (%s %% quantity), quantity"
                        "   FROM bulk_items"
                        "   WHERE bulkid = %s )")

        cursor = self._get_cursor()

        try:

            # Add zero inventories to everything that we didn't take inventory
            # on, or specifically mark to ignore, provided that the item is
            # active.
            nonzero_bulkids = tuple(
                self._protected.union(self._inventory.keys()))
            log.info(
                "nonzero_bulkids: {}".format(
                    ",".join(str(x) for x in nonzero_bulkids)))
            log.info(
                "protected: {}".format(
                    ",".join(str(x) for x in self._protected)))
            log.info(
                "inventory: {}".format(
                    ",".join(str(x) for x in self._inventory.keys())))
            log.info("set_zeros: {}".format(set_zeros))

            if set_zeros and nonzero_bulkids:
                log.info("Setting zeros on inventory")
                cursor.execute(blanks_query, [nonzero_bulkids])

            for bulkid in self._protected:
                # Sloppily delete pre-existing inventory for protected items
                cursor.execute(delete_query, [bulkid])

            for bulkid, quantity in self._inventory.items():
                # Sloppily delete any pre-existing inventory for this item from
                # today. This is because now we store full timestamps, but the
                # admin interface still expects dates, and I'm too lazy to do
                # it right. TODO
                cursor.execute(delete_query, [bulkid])

                cursor.execute(
                    valued_query, [quantity, quantity, quantity, bulkid])

            self._conn.commit()

        except psycopg2.IntegrityError:
            log.error("Rolling back due to integrity error.")
            self._conn.rollback()
            raise

        self._session.publish(PREFIX + 'committed', [])
        self.reset(False)

    def reset(self, announce):
        """Resets the inventory state to empty.
            - Everything disabled is un-disabled.
            - Everything inventoried is removed.
        """
        self._inventory.clear()
        self._protected.clear()
        if announce:
            self._announce_reset()


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

