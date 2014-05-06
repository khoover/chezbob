#!/usr/bin/env python3.4

import datetime
import soda_app
app = soda_app.app
db = soda_app.db

# This file contains the database models for all of the tables we use in the
# rest of the interface.  By importing the proper tables, other python modules
# can see these tables as basic python modules through SQLAlchemy.

# Currently included tables are:
#  aggregate_purchases
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
  userid = db.Column(db.Integer(), primary_key = True)
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
