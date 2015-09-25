#!/usr/bin/env python3.4

import datetime
import soda_app
import os
app = soda_app.app
db = soda_app.db

# This file contains the database models for all of the tables in te database.
# By importing the proper tables, other python modules
# can see these tables as basic python modules through SQLAlchemy.
# TODO: (dbounov) mark foreign keys
# TODO: (dbounov) document field constraints & insert them in constructors
# TODO: (dbounov) inter-table constraints

# Currently included tables are:
#  aggregate_purchases
#  bulk_items
#  finance_accounts
#  finance_deposit_summary
#  finance_inventory_summary
#  finance_splits
#  fingerprints 
#  floor_locations
#  historical_prices
#  inventory
#  messages
#  order_items
#  orders
#  products
#  profiles
#  transactions
#  userbarcodes
#  users

"""
  Table "public.aggregate_purchases"
  Column  |     Type      | Modifiers
----------+---------------+-----------
 date     | date          | not null
 barcode  | text          | not null
 quantity | integer       | not null
 price    | numeric(12,2) |
 bulkid   | integer       |
"""
class aggregate_purchases(db.Model):
  __tablename__ = 'aggregate_purchases'
  date = db.Column(db.Date(), primary_key=True)
  barcode = db.Column(db.String(), primary_key=True)
  quantity = db.Column(db.Integer())
  price = db.Column(db.Numeric(12,2))
  bulkid = db.Column(db.Integer())
  def __init__(self, barcode, price, bulkid):
        self.date = datetime.date.today()
        self.barcode = barcode
        self.quantity = 1
        self.price = price
        self.bulkid = bulkid

"""
  Table "public.bulk_items"
  Column        |     Type      | Modifiers
----------------+---------------+-----------
 bulkid         | integer       | not null
 description    | text          | not null
 price          | numeric(12,2) | not null
 taxable        | boolean       | not null
 quantity       | integer       | not null
 updated        | date          | default now()
 crv            | numeric(12,2) | 
 crv_taxable    | boolean       | not null
 source         | integer       | default 0 not null
 reserve        | integer       | default 0 not null
 active         | boolean       | default true not null
 floor_location | integer       | not null
 product_id     | text          | 
 crv_per_unit   | numeric(12,2) | 
 bulkbarcode    | character     | varying 
"""
class bulk_items(db.Model):
  __tablename__ = 'bulk_items'
  bulkid = db.Column(db.Integer(), db.Sequence('bulk_items_bulkid_seq'), primary_key = True)
  description = db.Column(db.String())
  price = db.Column(db.Numeric(12,2))
  taxable = db.Column(db.Boolean())
  quantity = db.Column(db.Integer())
  updated = db.Column(db.Date())
  crv = db.Column(db.Numeric(12,2))
  crv_taxable = db.Column(db.Boolean())
  source = db.Column(db.Integer())
  reserve = db.Column(db.Integer())
  active = db.Column(db.Boolean())
  floor_location = db.Column(db.Integer())
  product_id = db.Column(db.String())
  crv_per_unit = db.Column(db.Numeric(12,2))
  bulkbarcode = db.Column(db.String())


  def __init__(self, description, price, taxable, quantity, 
               crv, crv_taxable, source, reserve, active,
               floor_location, product_id, crv_per_unit, bulkbarcode):
        self.description = description
        self.price = price
        self.taxable = taxable
        self.quantity = quantity
        if (crv != None):
            self.crv = crv

        self.crv_taxable = crv_taxable
        if (source != None):
            self.source = source
        if (reserve != None):
            self.reserve = reserve
        if (active != None):
            self.active = active 

        self.floor_location = floor_location
        self.product_id = product_id
        self.crv_per_unit = crv_per_unit
        self.bulkbarcode = bulkbarcode

"""
  Table "public.finance_accounts"
  Column  |     Type                | Modifiers
----------+-------------------------+-----------
 id       | integer                 | not null
 type     | character varying(1)    | not null
 name     | character varying(256)  | not null
"""
class finance_accounts(db.Model):
  __tablename__ = 'finance_accounts'
  id = db.Column(db.Integer(), db.Sequence('finance_accounts_id_seq'), primary_key = True)
  type = db.Column(db.String())
  name = db.Column(db.String())
  def __init__(self, type, name):
        assert(len(type) == 1)
        self.type = type
        self.name = name 

"""
  Table "public.finance_deposit_summary"
  Column  |     Type                | Modifiers
----------+-------------------------+-----------
 date     | date                    | not null
 positive | numeric(12,2)           | not null
 negative | numeric(12,2)           | not null
"""
class finance_deposit_summary(db.Model):
  __tablename__ = 'finance_deposit_summary'
  date = db.Column(db.Date(), primary_key=True)
  positive = db.Column(db.Integer())
  negative = db.Column(db.Integer())

  def __init__(self, date, positive, negative):
        (self.date, self.positive, self.negative) =\
            (date, positive, negative)

"""
  Table "public.finance_inventory_summary"
  Column  |     Type                | Modifiers
----------+-------------------------+-----------
 date     | date                    | not null
 value    | numeric(12,2)           | not null
 shrinkage| numeric(12,2)           | not null
"""
class finance_inventory_summary(db.Model):
  __tablename__ = 'finance_inventory_summary'
  date = db.Column(db.Date(), primary_key=True)
  value = db.Column(db.Integer())
  shrinkage = db.Column(db.Integer())

  def __init__(self, date, value, shrinkage):
        (self.date, self.value, self.shrinkage) =\
            (date, value, shrinkage)

"""
  Table "public.finance_splits"
  Column         |     Type                | Modifiers
-----------------+-------------------------+-----------
 id              | integer                 | not null
 transaction_id  | integer                 | not null
 account_id      | integer                 | not null
 amount          | numeric(12,2)           | not null
 memo            | character varying(256)  | not null
"""
class finance_splits(db.Model):
  __tablename__ = 'finance_splits'
  id = db.Column(db.Integer(), db.Sequence('finance_splits_id_seq'), primary_key=True)
  transaction_id = db.Column(db.Integer())
  account_id = db.Column(db.Integer())
  amount = db.Column(db.Numeric(12,2))
  memo = db.Column(db.String())

  def __init__(self, transaction_id, account_id, amount, memo):
        (self.transaction_id, self.account_id, self.amount, self.memo) = \
            (transaction_id, account_id, amount, memo)

"""
                     Table "public.fingerprints"
 Column |  Type   | Modifiers | Storage  | Stats target | Description 
--------+---------+-----------+----------+--------------+-------------
 userid | integer | not null  | plain    |              | 
 fpdata | bytea   |           | extended |              | 
 fpimg  | bytea   |           | extended |              | 
Indexes:
    "fingerprints_pkey" PRIMARY KEY, btree (userid)
Has OIDs: no
"""
class fingerprints(db.Model):
  __tablename__ = 'fingerprints'
  userid = db.Column(db.Integer(), primary_key=True)
  fpdata = db.Column(db.LargeBinary())
  fpimg = db.Column(db.LargeBinary())

  def __init__(self, userid, fpdata, fpimg):
        (self.userid, self.fpdata, self.fpimg) = \
            (userid, fpdata, fpimg)

"""
                        Table "public.floor_locations"
 Column |       Type       | Modifiers | Storage  | Stats target | Description 
--------+------------------+-----------+----------+--------------+-------------
 id     | integer          | not null  | plain    |              | 
 name   | text             | not null  | extended |              | 
 markup | double precision | not null  | plain    |              | 
Indexes:
    "floor_locations_pkey" PRIMARY KEY, btree (id)
Referenced by:
    TABLE "bulk_items" CONSTRAINT "bulk_items_floor_location_fkey" FOREIGN KEY (floor_location) REFERENCES floor_locations(id)
Has OIDs: no
"""
class floor_locations(db.Model):
  __tablename__ = 'floor_locations'
  id = db.Column(db.Integer(), primary_key=True)
  name = db.Column(db.String())
  markup = db.Column(db.Float())

  def __init__(self, id, name, markup):
        (self.id, self.name, self.markup) = \
            (id, name, markup)

"""

                                                Table "public.historical_prices"
 Column |     Type      |                           Modifiers                            | Storage | Stats target | Description 
--------+---------------+----------------------------------------------------------------+---------+--------------+-------------
 bulkid | integer       | not null                                                       | plain   |              | 
 date   | date          | not null                                                       | plain   |              | 
 price  | numeric(12,2) | not null                                                       | main    |              | 
 id     | integer       | not null default nextval('historical_prices_id_seq'::regclass) | plain   |              | 
Indexes:
    "historic_prices_pkey" UNIQUE CONSTRAINT, btree (id)
    "historic_prices_lookup" btree (bulkid, date)
Foreign-key constraints:
    "historic_prices_bulkid_fkey" FOREIGN KEY (bulkid) REFERENCES bulk_items(bulkid)
Has OIDs: no
"""
class historical_prices(db.Model):
  __tablename__ = 'historical_prices'
  bulkid = db.Column(db.Integer())
  date = db.Column(db.Date())
  price = db.Column(db.Numeric(12,2))
  id = db.Column(db.Integer(), primary_key=True)

  def __init__(self, bulkid, date, price):
        (self.bulkid, self.date, self.price) = \
            (bulkid, date, price)

"""
                             Table "public.inventory"
   Column    |       Type       | Modifiers | Storage | Stats target | Description 
-------------+------------------+-----------+---------+--------------+-------------
 date        | date             | not null  | plain   |              | 
 bulkid      | integer          | not null  | plain   |              | 
 units       | integer          | not null  | plain   |              | 
 cases       | double precision |           | plain   |              | 
 loose_units | integer          |           | plain   |              | 
 case_size   | integer          | not null  | plain   |              | 
Indexes:
    "inventory_index" UNIQUE, btree (date, bulkid)
Foreign-key constraints:
    "inventory2_bulkid_fkey" FOREIGN KEY (bulkid) REFERENCES bulk_items(bulkid)
Has OIDs: no
"""
class inventory(db.Model):
  __tablename__ = 'inventory'
  date = db.Column(db.Date(), primary_key = True)
  bulkid = db.Column(db.Integer(), primary_key = True)
  units = db.Column(db.Integer())
  cases = db.Column(db.Float())
  loose_units = db.Column(db.Integer())
  case_size = db.Column(db.Integer())

  def __init__(self, date, bulkid, units, cases, loose_units, case_size):
    (self.date, self.bulkid, self.units, self.cases, self.loose_units, self.case_size) = \
        (date, bulkid, units, cases, loose_units, case_size)

"""
                                Table "public.messages"
 Column  |           Type           | Modifiers | Storage  | Stats target | Description 
---------+--------------------------+-----------+----------+--------------+-------------
 msgid   | integer                  | not null  | plain    |              | 
 msgtime | timestamp with time zone | not null  | plain    |              | 
 userid  | integer                  |           | plain    |              | 
 message | character varying        | not null  | extended |              | 
Indexes:
    "messages_pkey" PRIMARY KEY, btree (msgid)
Has OIDs: no
"""
class messages(db.Model):
  __tablename__ = 'messages'
  msgid = db.Column(db.Integer(), db.Sequence('msgid_seq'), primary_key = True)
  msgtime = db.Column(db.DateTime())
  userid = db.Column(db.Integer())
  message = db.Column(db.String())

  def __init__(self, msgtime, userid, message):
    (self.msgtime, self.userid, self.message) = \
        (msgtime, userid, message)

"""
                                                     Table "public.order_items"
      Column      |     Type      |                        Modifiers                         | Storage | Stats target | Description 
------------------+---------------+----------------------------------------------------------+---------+--------------+-------------
 id               | integer       | not null default nextval('order_items_id_seq'::regclass) | plain   |              | 
 order_id         | integer       | not null                                                 | plain   |              | 
 bulk_type_id     | integer       | not null                                                 | plain   |              | 
 quantity         | integer       | not null                                                 | plain   |              | 
 number           | integer       | not null                                                 | plain   |              | 
 case_cost        | numeric(12,2) | not null default 0.00                                    | main    |              | 
 crv_per_unit     | numeric(12,2) | not null default 0.00                                    | main    |              | 
 is_cost_taxed    | boolean       | not null default false                                   | plain   |              | 
 is_crv_taxed     | boolean       | not null default false                                   | plain   |              | 
 is_cost_migrated | boolean       | not null default false                                   | plain   |              | 
Indexes:
    "order_items_pkey" PRIMARY KEY, btree (id)
Foreign-key constraints:
    "order_id_referencing_orders_id" FOREIGN KEY (order_id) REFERENCES orders(id)
    "order_items_bulk_type_id_fkey" FOREIGN KEY (bulk_type_id) REFERENCES bulk_items(bulkid)
Has OIDs: no
"""
class order_items(db.Model):
  __tablename__ = 'order_items'
  id = db.Column(db.Integer(), primary_key = True)
  order_id = db.Column(db.Integer())
  bulk_type_id = db.Column(db.Integer())
  quantity = db.Column(db.Integer())
  number = db.Column(db.Integer())
  case_cost = db.Column(db.Numeric(12,2))
  crv_per_unit = db.Column(db.Numeric(12,2))
  is_cost_taxed = db.Column(db.Boolean())
  is_crv_taxed = db.Column(db.Boolean())
  is_cost_migrated = db.Column(db.Boolean())

  def __init__(self, order_id, bulk_type_id, quantity, number, case_cost,
        crv_per_unit, is_cost_taxed, is_crv_taxed, is_cost_migrated):
        (self.order_id, self.bulk_type_id, self.quantity, self.number,
         self.case_cost, self.crv_per_unit, self.is_cost_taxed,
         self.is_crv_taxed, self.is_cost_migrated) = \
            (order_id, bulk_type_id, quantity, number, case_cost,
                crv_per_unit, is_cost_taxed, is_crv_taxed, is_cost_migrated)


"""
                                                             Table "public.orders"
         Column         |          Type          |                      Modifiers                      | Storage  | Stats target | Description 
------------------------+------------------------+-----------------------------------------------------+----------+--------------+-------------
 id                     | integer                | not null default nextval('orders_id_seq'::regclass) | plain    |              | 
 date                   | date                   | not null                                            | plain    |              | 
 description            | character varying(256) | not null                                            | extended |              | 
 amount                 | numeric(12,2)          | not null                                            | main     |              | 
 tax_rate               | numeric(6,4)           | not null                                            | main     |              | 
 inventory_adjust       | numeric(12,2)          | default 0                                           | main     |              | 
 supplies_adjust        | numeric(12,2)          | default 0                                           | main     |              | 
 supplies_taxed         | numeric(12,2)          | default 0                                           | main     |              | 
 supplies_nontaxed      | numeric(12,2)          | default 0                                           | main     |              | 
 returns_taxed          | numeric(12,2)          | default 0                                           | main     |              | 
 returns_nontaxed       | numeric(12,2)          | default 0                                           | main     |              | 
 finance_transaction_id | integer                |                                                     | plain    |              | 
Indexes:
    "orders_pkey" PRIMARY KEY, btree (id)
Foreign-key constraints:
    "orders_finance_transaction_fkey" FOREIGN KEY (finance_transaction_id) REFERENCES finance_transactions(id)
Referenced by:
    TABLE "order_items" CONSTRAINT "order_id_referencing_orders_id" FOREIGN KEY (order_id) REFERENCES orders(id)
Has OIDs: no
"""
class orders(db.Model):
  __tablename__ = 'orders'
  id = db.Column(db.Integer(), primary_key = True)
  date = db.Column(db.Date())
  description = db.Column(db.String())
  amount = db.Column(db.Numeric(12,2))
  tax_rate = db.Column(db.Numeric(6,4))
  inventory_adjust = db.Column(db.Numeric(12,2))
  supplies_adjust = db.Column(db.Numeric(12,2))
  supplies_taxed = db.Column(db.Numeric(12,2))
  supplies_nontaxed = db.Column(db.Numeric(12,2))
  returns_taxed = db.Column(db.Numeric(12,2))
  returns_nontaxed = db.Column(db.Numeric(12,2))
  finance_transaction_id = db.Column(db.Integer())

  def __init__(self, date, description, amount, tax_rate, inventory_adjust,
      supplies_adjust, supplies_taxed, supplies_nontaxed, returns_taxed,
      returns_nontaxed, finance_transaction_id):
    (self.date, self.description, self.amount, self.tax_rate, self.inventory_adjust,
      self.supplies_adjust, self.supplies_taxed, self.supplies_nontaxed, self.returns_taxed,
      self.returns_nontaxed, self.finance_transaction_id) = \
         (date, description, amount, tax_rate, inventory_adjust,
          supplies_adjust, supplies_taxed, supplies_nontaxed, returns_taxed,
          returns_nontaxed, finance_transaction_id)
    
"""
                                                             Table "public.product_source"
       Column       |         Type          |                             Modifiers                             | Storage  | Stats target | Description 
--------------------+-----------------------+-------------------------------------------------------------------+----------+--------------+-------------
 sourceid           | integer               | not null default nextval('product_source_sourceid_seq'::regclass) | plain    |              | 
 source_description | character varying(50) |                                                                   | extended |              | 
Indexes:
    "product_source_pkey" PRIMARY KEY, btree (sourceid)
Has OIDs: no
"""
class product_source(db.Model):
  __tablename__ = 'product_source'
  sourceid = db.Column(db.Integer(), db.Sequence('product_source_sourceid_seq'), primary_key=True)
  source_description = db.Column(db.String())

  # TODO (dbounov) product_source_sourceid_seq seems to be out of sync with the values in the table
  # Once we fix this remove sourceid from constructor arguments.
  def __init__(self, sourceid, source_description):
    self.source_description = source_description
    self.sourceid = sourceid

"""

                               Table "public.products"
    Column     |       Type        |       Modifiers        | Storage  | Description
---------------+-------------------+------------------------+----------+-------------
 barcode       | character varying | not null               | extended |
 name          | character varying | not null               | extended |
 phonetic_name | character varying | not null               | extended |
 price         | numeric(12,2)     | not null               | main     |
 bulkid        | integer           |                        | plain    |
 coffee        | boolean           | not null default false | plain    |
"""
class products(db.Model):
  __tablename__ = 'products'
  barcode = db.Column(db.String(), primary_key = True)
  name = db.Column(db.String())
  phonetic_name = db.Column(db.String())
  price = db.Column(db.Numeric(12,2))
  bulkid = db.Column(db.Integer())
  coffee = db.Column(db.Boolean())

  def __init__(self, barcode, name, phonetic_name, price, bulkid, coffee):
    (self.barcode, self.name, self.phonetic_name, self.price, self.bulkid,\
     self.coffee) = \
        (barcode, name, phonetic_name, price, bulkid, coffee)
    

"""
                      Table "public.profiles"
  Column  |       Type        | Modifiers | Storage  | Description
----------+-------------------+-----------+----------+-------------
 userid   | integer           | not null  | plain    |
 property | character varying | not null  | extended |
 setting  | integer           | not null  | plain    |
"""
class profiles(db.Model):
  __tablename__ = 'profiles'
  userid = db.Column(db.Integer(), primary_key = True)
  property = db.Column(db.String(), primary_key = True)
  setting = db.Column(db.Integer())

  def __init__(self, userid, property, setting):
    (self.userid, self.property, self.setting) = \
          (userid, property, setting)

"""
              Table "public.roles"
 Column  |  Type   | Modifiers             | Storage  | Description
---------+---------+-----------------------+----------+-------------
 userid  | integer | not null primary key  | plain    |
 roles   | text    | not null              | extended | comma separated list of roles from {resocker,}

"""
class roles(db.Model):
  __tablename__ = 'roles'
  userid = db.Column(db.Integer(), primary_key = True)
  roles = db.Column(db.String())

  def __init__(self, userid, roles):
    self.userid = userid;
    self.roles = roles

"""
              Table "public.soda_inventory"
 Column  |  Type                | Modifiers    | Storage  | Description
---------+----------------------+--------------+----------+-------------
 slot    | character varying(2) | primary key  | plain    |
 count   | int                  | not null     | plain    |

"""
class soda_inventory(db.Model):
  __tablename__ = 'soda_inventory'
  slot = db.Column(db.String(), primary_key = True)
  count = db.Column(db.Integer())

  def __init__(self, slot, count):
    assert (len(slot) <= 2)
    self.slot = slot
    self.count = count
    
"""
                                                   Table "public.transactions"
      Column      |           Type           |                         Modifiers                         | Storage  | Description
------------------+--------------------------+-----------------------------------------------------------+----------+-------------
 xacttime         | timestamp with time zone | not null                                                  | plain    |
 userid           | integer                  | not null                                                  | plain    |
 xactvalue        | numeric(12,2)            | not null                                                  | main     |
 xacttype         | character varying        | not null                                                  | extended |
 barcode          | character varying        |                                                           | extended |
 source           | character varying        |                                                           | extended |
 id               | integer                  | not null default nextval('transactions_id_seq'::regclass) | plain    |
 finance_trans_id | integer                  |                                                           | plain    |
"""
class transactions(db.Model):
  __tablename__ = 'transactions'
  xacttime = db.Column(db.DateTime(True))
  userid = db.Column(db.Integer())
  xactvalue = db.Column(db.String())
  xacttype = db.Column(db.String())
  barcode = db.Column(db.String(), nullable = True)
  source = db.Column(db.String(), nullable = True)
  id = db.Column(db.Integer(), primary_key = True)
  finance_trans_id = db.Column(db.Integer(), nullable = True)
  def __init__(self, userid, xactvalue, xacttype, barcode, source, finance_trans_id = None):
        self.userid = userid
        self.xactvalue = xactvalue
        self.xacttype = xacttype
        self.barcode = barcode
        self.source = source
        self.finance_trans_id = finance_trans_id
        self.xacttime = datetime.datetime.now()

"""
                     Table "public.ucsd_emails"
  Column  | Type | Modifiers | Storage  | Stats target | Description 
----------+------+-----------+----------+--------------+-------------
 username | text |           | extended |              | 
Has OIDs: no
"""
class ucsd_emails(db.Model):
  __tablename__ = 'ucsd_emails'
  username = db.Column(db.String(), primary_key = True)

  def __init__(self, username):
    self.username = username

"""
              Table "public.userbarcodes"
 Column  |  Type   | Modifiers | Storage  | Description
---------+---------+-----------+----------+-------------
 userid  | integer | not null  | plain    |
 barcode | text    | not null  | extended |
"""
class userbarcodes(db.Model):
  __tablename__ = 'userbarcodes'
  userid = db.Column(db.Integer())
  barcode = db.Column(db.String(), primary_key = True)

  def __init__(self, userid, barcode):
    self.userid = userid
    self.barcode = barcode

"""
                                             Table "public.users"
           Column           |            Type             |         Modifiers         | Storage  | Description
----------------------------+-----------------------------+---------------------------+----------+-------------
 userid                     | integer                     | not null                  | plain    |
 username                   | character varying           | not null                  | extended |
 email                      | character varying           | not null                  | extended |
 nickname                   | character varying           |                           | extended |
 pwd                        | text                        |                           | extended |
 balance                    | numeric(12,2)               | not null default 0.00     | main     |
 disabled                   | boolean                     | not null default false    | plain    |
 last_purchase_time         | timestamp with time zone    |                           | plain    |
 last_deposit_time          | timestamp with time zone    |                           | plain    |
 pref_auto_logout           | boolean                     | not null default false    | plain    |
 pref_speech                | boolean                     | not null default false    | plain    |
 pref_forget_which_product  | boolean                     | not null default false    | plain    |
 pref_skip_purchase_confirm | boolean                     | not null default false    | plain    |
 notes                      | text                        | not null default ''::text | extended |
 created_time               | timestamp without time zone | default now()             | plain    |
 fraudulent                 | boolean                     | not null default false    | plain    |
"""
class users(db.Model):
  __tablename__ = 'users'
  userid = db.Column(db.Integer(), db.Sequence('userid_seq'), primary_key = True)
  username = db.Column(db.String())
  email = db.Column(db.String())
  nickname = db.Column(db.String(), nullable = True)
  pwd = db.Column(db.String())
  balance = db.Column(db.Numeric(12,2))
  disabled = db.Column(db.Boolean())
  last_purchase_time = db.Column(db.DateTime(True))
  last_deposit_time = db.Column(db.DateTime(True))
  pref_auto_logout = db.Column(db.Boolean())
  pref_speech = db.Column(db.Boolean())
  pref_forget_which_product = db.Column(db.Boolean())
  pref_skip_purchase_confirm = db.Column(db.Boolean())
  notes = db.Column(db.String())
  created_time = db.Column(db.DateTime())
  fraudulent = db.Column(db.Boolean())

  def __init__(self, username, email, nickname, pwd, balance, disabled,
    last_purchase_time, last_deposit_time, pref_auto_logout, pref_speech,
    pref_forget_which_product, pref_skip_purchase_confirm, notes,
    created_time, fraudulent):
    self.username = username
    self.email = email
    self.nickname = nickname
    self.pwd = pwd
    self.balance = balance
    self.disabled = disabled
    self.last_purchase_time = last_purchase_time
    self.last_deposit_time = last_deposit_time
    self.pref_auto_logout = pref_auto_logout
    self.pref_speech = pref_speech
    self.pref_forget_which_product = pref_forget_which_product
    self.pref_skip_purchase_confirm = pref_skip_purchase_confirm
    self.notes = notes
    self.created_time = created_time
    self.fraudulent = fraudulent
