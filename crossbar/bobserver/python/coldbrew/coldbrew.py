import psycopg2
import psycopg2.extras

from twisted.internet.defer import inlineCallbacks
from twisted.logger import Logger

#from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession
#from autobahn.wamp.exception import ApplicationError

from sh import mail

DB_CREDS = {"dbname": "bob", "user": "bob", "host": "localhost"}

PURCHASE_BARCODE = '488348702402'
OUT_OF_ORDER_BARCODE = '487846576652'
IN_TO_ORDER_BARCODE = '409001323468'

WARN_LEVEL = 80

MAIL_FROM = "Coldbrew Bot <coldbrew@chezbob.ucsd.edu>"
MAIL_REPLY_TO = "cse-coldbrew@eng.ucsd.edu"
MAIL_TO = "cse-coldbrew@eng.ucsd.edu"
MAIL_SUBJECT = "Coldbrew Stock Low"
MAIL_MSG = """Hi Coldbrewers,

There have been {n_sold} cups of coldbrew sold on the current keg.

It may be running low!

Love,
Coldbrew Bot
"""


def send_mail(to, subject, msg, frm, reply_to=None):
    args = ['-a', "From: {}".format(frm), '-s', subject, to]
    if reply_to:
        args = ['-a', 'Reply-To: {}'.format(reply_to)] + args
    mail(*args, _in=msg)


class AppSession(ApplicationSession):

    log = Logger()

    def __init__(self, *args, **kwargs):
        self.conn = psycopg2.connect(**DB_CREDS)
        self.conn.set_client_encoding("utf-8")
        self._n_sold = self._n_sold_since_last_restock()
        super().__init__(*args, **kwargs)

    def _n_sold_since_last_restock(self):
        """Returns number of coldbrew cups sold since last restock."""

        query = ("select count(*) from transactions"
                 " where barcode = %s"
                 " and xacttime >"
                 "  (select xacttime from transactions t"
                 "   where barcode in (select barcode from coldbrew_varieties)"
                 "   order by xacttime desc limit 1)")

        cursor = self.conn.cursor()
        cursor.execute(query, [PURCHASE_BARCODE])
        self.conn.commit()
        return cursor.fetchone()[0]

    def _get_most_recent_restock_code(self):
        """Returns most recent barcode used to restock the cold brew."""

        query = ("select barcode from transactions"
                 " where barcode in (select barcode from coldbrew_varieties)"
                 " order by xacttime desc limit 1")

        cursor = self.conn.cursor()
        cursor.execute(query, [])
        self.conn.commit()
        return cursor.fetchone()[0]

    def _is_out_of_order(self):
        """Returns whether or not we're in or out of order."""

        query = ("select barcode from transactions"
                 " where barcode in %s"
                 " order by xacttime desc limit 1")

        cursor = self.conn.cursor()
        cursor.execute(query, [(IN_TO_ORDER_BARCODE, OUT_OF_ORDER_BARCODE)])
        self.conn.commit()

        if not cursor.rowcount:
            return False

        bc = cursor.fetchone()[0]

        if bc == OUT_OF_ORDER_BARCODE:
            return True
        return False

    def _get_keg_details_from_bc(self, bc):
        """Returns most recent barcode used to restock the cold brew."""

        query = ("select name, description from coldbrew_varieties"
                 " where barcode = %s")

        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(query, [bc])
        self.conn.commit()

        if cursor.rowcount:
            return cursor.fetchone()
        return None

    def get_keg_status(self):
        """Returns the state of the current cold brew keg.

        Returns dictionary including name, description and n_sold:
            - name/description of current coffee variety
            - number of cups sold on that keg.
        """
        name, description = (None, None)
        restock_bc = self._get_most_recent_restock_code()
        details = self._get_keg_details_from_bc(restock_bc)
        if details:
            name, description = list(details)
        self._n_sold = self._n_sold_since_last_restock()

        ooo = self._is_out_of_order()

        return {"name": name, "description": description,
                "n_sold": self._n_sold, "out_of_order": ooo}

    @inlineCallbacks
    def onJoin(self, details):
        self.log.info("Starting coldbrew...")

        yield self.register(
            self.get_keg_status,
            'chezbob.coldbrew.get_keg_status')

        # Catch transactions, then republish the relevant ones reformatted.
        yield self.subscribe(self.process_transactions, 'chezbob.transaction')

    def prepare_activity_record(self, record):
        if record['t_barcode'] == PURCHASE_BARCODE:
            self._n_sold += 1
            return {"type": "purchase"}

        if record['t_barcode'] == OUT_OF_ORDER_BARCODE:
            return {"type": "out_of_order"}

        if record['t_barcode'] == IN_TO_ORDER_BARCODE:
            return {"type": "in_to_order"}

        details = self._get_keg_details_from_bc(record['t_barcode'])
        if details:
            self._n_sold = 0
            return {"type": "restock",
                    "name": details[0], "description": details["description"]}

        return None

    def process_transactions(self, record):
        activity = self.prepare_activity_record(record)
        # Drop non-coldbrew activity
        if not activity:
            return

        # Real quick, email the list if we're at the warn level.
        if self._n_sold == WARN_LEVEL:
            msg = MAIL_MSG.format(n_sold=self._n_sold)
            send_mail(MAIL_TO, MAIL_SUBJECT, msg, MAIL_FROM, MAIL_REPLY_TO)

        # Publish out the changes to the world.
        return self.publish('chezbob.coldbrew.activity', activity)

