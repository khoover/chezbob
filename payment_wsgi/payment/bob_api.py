"""This is just to get up and running.

Sorry. Roll with it.
"""

import psycopg2
import sys


class InvalidOperationException(Exception):
    pass


class BobApi(object):
    def __init__(self, creds):
        self.db = psycopg2.connect(**creds)
        self.cursor = self.db.cursor()

    def is_valid_username(self, username):
        """Given a username, return whether or not it's valid. """
        return self.get_userid(username) is not None

    def get_balance(self, username):
        """Given a username, returns their balance, or None. """
        query = ("SELECT balance FROM users WHERE username = %s")
        self.cursor.execute(query, [username])

        if self.cursor.rowcount > 0:
            return float(self.cursor.fetchone()[0])
        return None

    def get_userid(self, username):
        """Given a username, return userid or None if invalid. """
        query = ("SELECT userid FROM users WHERE username = %s")
        self.cursor.execute(query, [username])

        if self.cursor.rowcount > 0:
            return self.cursor.fetchone()[0]
        return None

    def make_deposit(self, username, amount):
        """Deposits the given amount into the username provided."""
        if amount < 0:
            raise InvalidOperationException("invalid amount for deposit")

        userid = self.get_userid(username)
        if not userid:
            raise InvalidOperationException("invalid username")

        query1 = ("UPDATE users SET balance = balance + %s WHERE userid = %s")
        query2 = ("INSERT INTO transactions"
                  " (xacttime, userid, xactvalue, xacttype, source)"
                  " VALUES"
                  " (now(), %s, %s, 'ADD BY CC', 'webpayment')")
        self.cursor.execute(query1, [amount, userid])
        self.cursor.execute(query2, [userid, amount])
        self.db.commit()


def main():
    pass

if __name__ == "__main__":
    sys.exit(main())
