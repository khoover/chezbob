
import sys

sys.path.append('/git/pybob/db/')

from datetime import date, datetime
from models import *

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bob@localhost:5432/bob'
#
# Simple test that for each table queries all entries, creates a new entry
# with default values, and then removes it.
#
# TODO: querying all aggregate_purchases causes python to die
# TODO: these defaults include foreign-key references. These were
#   written assuming a normal database dump. Fix this to
#   work on an arbitrary database without leaving crud.
#

valid_bulkid = 207
valid_userid = 1757
valid_orderid = 1
valid_finance_transaction_id = 1

default = {
    # AggregatePurchases: ( ) ,
    BulkItems: ('description', 1.00, True, 1, 1.00, True, 1, 0, True,
                1, 1, 1.00, 'barcode'),
    FinanceAccounts: ('D', 'name'),
    FinanceDepositSummary: (date(2015, 9, 10), 1.00, 1.00),
    FinanceInventorySummary: (date(2015, 9, 10), 1.00, 1.00),
    FinanceSplits: (1, 1, 1.00, "memo"),
    Fingerprints: (1, b'0x0', b'0x0'),
    FloorLocations: (100, 'name', 1.00),
    HistoricalPrices: (valid_bulkid, date(2015, 9, 10), 1.00),
    Inventory: (date(2015, 9, 10), valid_bulkid, 1, 1.00, 1, 1),
    Messages: (datetime(2015, 9, 10), valid_userid, 'message'),
    OrderItems: (valid_orderid, valid_bulkid, 1, 1, 1.00, 1.00,
                 True, True, True),
    Orders: (date(2015, 9, 10), 'description', 1.00, 1.00,
             1.00, 1.00, 1.00, 1.00, 1.00, 1.00,
             valid_finance_transaction_id),
    ProductSource: (100, 'source_desription',),
    Products: ('barcode', 'name', 'phonetic name', 1.00,
               valid_bulkid, False),
    Profiles: (valid_userid, 'property', 1),
    Roles: (valid_userid, 'roles'),
    SodaInventory: ('99', 1),
    Transactions: (valid_userid, 1.00,
                   'transaction type', 'barcode', 'source',
                   valid_finance_transaction_id),
    UCSDEmails: ('username',),
    UserBarcodes: (valid_userid, 'barcode'),
    Users: ('username', 'username@dummy.ucsd', 'nickname',
            'password', 0.00, False, datetime(2015, 9, 10),
            datetime(2015, 9, 10), False, False, False, False,
            'notes', datetime(2015, 9, 10), False)
}


def main():
    for tbl in (
            # AggregatePurchases,
            BulkItems,
            FinanceAccounts,
            FinanceDepositSummary,
            FinanceInventorySummary,
            FinanceSplits,
            Fingerprints,
            FloorLocations,
            HistoricalPrices,
            Inventory,
            Messages,
            OrderItems,
            Orders,
            ProductSource,
            Products,
            Profiles,
            Roles,
            SodaInventory,
            Transactions,
            UCSDEmails,
            UserBarcodes,
            Users
    ):
        print ("Testing ", tbl.__tablename__)
        all = tbl.query.all()
        print ("    Found %d entries" % len(all))
        new = tbl(*default[tbl])
        print ("    Created a new entry")
        db.session.add(new)
        db.session.commit()
        print ("    Inserted new entry")
        db.session.delete(new)
        db.session.commit()
        print ("    Deleted new entry")

if __name__ == "__main__":
    main()

