import sys;

sys.path.append('/git/pybob/db/')

from models import *
from datetime import date, datetime

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bob@localhost:5432/bob'
#
# Simple test that for each table queries all entries, creates a new entry
# with default values, and then removes it.
#
# TODO: querying all aggregate_purchases causes python to die
# TODO: these defaults include foreign-key references. These were
#	written assuming a normal database dump. Fix this to
# 	work on an arbitrary database without leaving crud.
#

valid_bulkid = 207
valid_userid = 1757
valid_orderid = 1
valid_finance_transaction_id = 1

default = {
#	aggregate_purchases: ( ) ,
	bulk_items: ('description', 1.00, True, 1, 1.00, True, 1, 0, True,
		1, 1, 1.00, 'barcode'),
	finance_accounts: ('D', 'name'),
	finance_deposit_summary: (date(2015, 9, 10), 1.00, 1.00),
	finance_inventory_summary: (date(2015, 9, 10), 1.00, 1.00),
	finance_splits: (1, 1, 1.00, "memo"),
	fingerprints: (1, b'0x0', b'0x0'),
	floor_locations: (100, 'name', 1.00),
	historical_prices: (valid_bulkid, date(2015, 9, 10), 1.00),
	inventory: (date(2015,9,10), valid_bulkid, 1, 1.00, 1, 1),
	messages: (datetime(2015,9,10), valid_userid, 'message'),
	order_items: (valid_orderid, valid_bulkid, 1, 1, 1.00, 1.00,\
		True, True, True),
	orders:	(date(2015,9,10), 'description', 1.00, 1.00, \
		1.00, 1.00, 1.00, 1.00, 1.00, 1.00, \
		valid_finance_transaction_id),
	product_source: (100, 'source_desription',),
	products: ('barcode', 'name', 'phonetic name', 1.00,
		valid_bulkid, False),
	profiles: (valid_userid, 'property', 1),
	roles: (valid_userid, 'roles'),
	soda_inventory: ('99', 1),
	transactions: (valid_userid, 1.00,\
		'transaction type', 'barcode', 'source', \
		 valid_finance_transaction_id),\
	ucsd_emails: ('username',),\
	userbarcodes: (valid_userid, 'barcode'),\
	users: ('username', 'username@dummy.ucsd', 'nickname',\
		'password', 0.00, False, datetime(2015,9,10),\
		datetime(2015,9,10), False, False, False, False,\
		'notes', datetime(2015,9,10), False)
}

for tbl in (\
	#aggregate_purchases,\
	bulk_items,\
	finance_accounts,\
	finance_deposit_summary,\
	finance_inventory_summary,\
	finance_splits,\
	fingerprints,\
	floor_locations,\
	historical_prices,\
	inventory,\
	messages,\
	order_items,\
	orders,\
	product_source,\
	products,\
	profiles,\
	roles,\
	soda_inventory,\
	transactions,\
	ucsd_emails,\
	userbarcodes,\
	users,\
	):
	print ("Testing ", tbl.__tablename__)
	all = tbl.query.all()
	print ("    Found %d entries" % len(all))
	new = tbl(*default[tbl])
	print ("    Created a new entry")
	db.session.add(new)
	db.session.commit();
	print ("    Inserted new entry")
	db.session.delete(new)
	db.session.commit();
	print ("    Deleted new entry")
