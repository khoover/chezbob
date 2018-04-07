"""This is just to get up and running.

Sorry. Roll with it.
"""

import psycopg2
import psycopg2.extras


class InvalidOperationException(Exception):
    pass


class BobApi(object):
    def __init__(self, creds, connected=False):
        if type(creds) == psycopg2.extensions.connection:
            self.db = creds
        else:
            self.db = psycopg2.connect(**creds)
        self.db.set_client_encoding('utf8')

    def _get_cursor(self):
        return self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def is_valid_username(self, username):
        """Given a username, return whether or not it's valid. """
        return self.get_userid(username) is not None

    def get_balance(self, username):
        """Given a username, returns their balance, or None. """
        query = ("SELECT balance FROM users WHERE username = %s")
        cursor = self._get_cursor()
        cursor.execute(query, [username])

        if cursor.rowcount > 0:
            return cursor.fetchone()[0]
        return None

    def get_userid(self, username):
        """Given a username, return userid or None if invalid. """
        query = ("SELECT userid FROM users WHERE username = %s")
        cursor = self._get_cursor()
        cursor.execute(query, [username])

        if cursor.rowcount > 0:
            return cursor.fetchone()[0]
        return None

    def make_deposit(self, username, amount, description, source=None):
        """Deposits the given amount into the username provided."""
        if amount < 0:
            raise InvalidOperationException("invalid amount for deposit")

        userid = self.get_userid(username)
        if not userid:
            raise InvalidOperationException("invalid username")

        if not source:
            source = 'webpayment'

        description = "ADD " + description

        query1 = ("UPDATE users SET balance = balance + %s WHERE userid = %s")
        query2 = ("INSERT INTO transactions"
                  " (xacttime, userid, xactvalue, xacttype, source)"
                  " VALUES"
                  " (now(), %s, %s, %s, %s)")
        cursor = self._get_cursor()
        cursor.execute(query1, [amount, userid])
        cursor.execute(query2, [userid, amount, description, source])
        self.db.commit()

    def get_day_stats(self):
        """Returns stats from the past day."""

        query = (" SELECT"
                 "  count(*) as n_transactions,"
                 "  sum(case when xactvalue < 0 then 1 else 0 end) as n_purchases,"
                 "  sum(case when xactvalue < 0 then xactvalue else 0 end) as purchased,"
                 "  sum(case when xactvalue > 0 then 1 else 0 end) as n_deposits,"
                 "  sum(case when xactvalue > 0 then xactvalue else 0 end) as deposits,"
                 "  sum(xactvalue) as net"
                 " from transactions"
                 " where"
                 "  xacttime >= now() - interval '24 hours'"
                 )

        cursor = self._get_cursor()
        cursor.execute(query)
        stats = cursor.fetchone()
        return stats

    def get_deposited_cash(self):
        """Returns the expected makeup of cash sitting in soda machine."""

        since = self._get_last_soda_empty()
        query = (" SELECT"
                 "  xactvalue::integer::text as value,"
                 "  count(*) as n,"
                 "  (count(*) * xactvalue) as total"
                 " from transactions"
                 " where"
                 "  xactvalue >= 1"
                 "  and xacttime > %s"
                 "  and source = 'bob2k14.2'"
                 "  and xacttype like 'ADD %% (cash)'"
                 " group by xactvalue"
                 " order by xactvalue")

        cursor = self._get_cursor()
        try:
            cursor.execute(query, [since])
        except:
            import traceback
            traceback.print_exc()

        rows = cursor.fetchall()
        return rows

    def _get_last_soda_empty(self):
        query = (
            " SELECT"
            "     max(xacttime) as last_emptied"
            " FROM transactions WHERE barcode = '482665976515'")
        return self._fetchone(query)['last_emptied']

    def _fetchone(self, query, *args, **kwargs):
        cursor = self._get_cursor()
        try:
            cursor.execute(query, *args, **kwargs)
        except:
            import traceback
            traceback.print_exc()

        if cursor.rowcount:
            row = cursor.fetchone()
        else:
            row = None
        self.db.commit()
        return row

