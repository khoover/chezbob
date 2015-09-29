#!/usr/bin/env python3.4

import datetime

import soda_app

app = soda_app.app
db = soda_app.db

# This file contains the database models for all of the tables in te database.
# By importing the proper tables, other python modules
# can see these tables as basic python modules through SQLAlchemy.
# TODO: (dbounov) mark foreign keys
# TODO: (dbounov) document field constraints & insert them in constructors
# TODO: (dbounov) inter-table constraints

# TODO: (jdeblasio) proper docstrings for classes and for overall module.
# TODO: (jdeblasio) disable need for docstrings in __init__ functions.

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


class AggregatePurchases(db.Model):

    # TODO: Docstring

    __tablename__ = 'aggregate_purchases'
    date = db.Column(db.Date(), primary_key=True)
    barcode = db.Column(db.String(), primary_key=True)
    quantity = db.Column(db.Integer())
    price = db.Column(db.Numeric(12, 2))
    bulkid = db.Column(db.Integer())

    def __init__(self, barcode, price, bulkid):
        # TODO: Docstring
        self.date = datetime.date.today()
        self.barcode = barcode
        self.quantity = 1
        self.price = price
        self.bulkid = bulkid


class BulkItems(db.Model):

    # TODO: Docstring

    __tablename__ = 'bulk_items'
    bulkid = db.Column(
        db.Integer(), db.Sequence('bulk_items_bulkid_seq'), primary_key=True)
    description = db.Column(db.String())
    price = db.Column(db.Numeric(12, 2))
    taxable = db.Column(db.Boolean())
    quantity = db.Column(db.Integer())
    updated = db.Column(db.Date())
    crv = db.Column(db.Numeric(12, 2))
    crv_taxable = db.Column(db.Boolean())
    source = db.Column(db.Integer())
    reserve = db.Column(db.Integer())
    active = db.Column(db.Boolean())
    floor_location = db.Column(db.Integer())
    product_id = db.Column(db.String())
    crv_per_unit = db.Column(db.Numeric(12, 2))
    bulkbarcode = db.Column(db.String())

    def __init__(self, description, price, taxable, quantity,
                 crv, crv_taxable, source, reserve, active,
                 floor_location, product_id, crv_per_unit, bulkbarcode):
        # TODO: Docstring
        self.description = description
        self.price = price
        self.taxable = taxable
        self.quantity = quantity
        if crv is not None:
            self.crv = crv

        self.crv_taxable = crv_taxable
        if source is not None:
            self.source = source
        if reserve is not None:
            self.reserve = reserve
        if active is not None:
            self.active = active

        self.floor_location = floor_location
        self.product_id = product_id
        self.crv_per_unit = crv_per_unit
        self.bulkbarcode = bulkbarcode


class FinanceAccounts(db.Model):

    # TODO: Docstring

    __tablename__ = 'finance_accounts'
    id = db.Column(db.Integer(), db.Sequence(
        'finance_accounts_id_seq'), primary_key=True)
    type = db.Column(db.String())
    name = db.Column(db.String())

    def __init__(self, type, name):
        # TODO: Docstring
        assert(len(type) == 1)
        self.type = type
        self.name = name


class FinanceDepositSummary(db.Model):

    # TODO: Docstring

    __tablename__ = 'finance_deposit_summary'
    date = db.Column(db.Date(), primary_key=True)
    positive = db.Column(db.Integer())
    negative = db.Column(db.Integer())

    def __init__(self, date, positive, negative):
        # TODO: Docstring
        self.date = date
        self.positive = positive
        self.negative = negative


class FinanceInventorySummary(db.Model):

    # TODO: Docstring

    __tablename__ = 'finance_inventory_summary'
    date = db.Column(db.Date(), primary_key=True)
    value = db.Column(db.Integer())
    shrinkage = db.Column(db.Integer())

    def __init__(self, date, value, shrinkage):
        # TODO: Docstring
        self.date = date
        self.value = value
        self.shrinkage = shrinkage


class FinanceSplits(db.Model):
    # TODO: Docstring
    __tablename__ = 'finance_splits'
    id = db.Column(
        db.Integer(), db.Sequence('finance_splits_id_seq'), primary_key=True)
    transaction_id = db.Column(db.Integer())
    account_id = db.Column(db.Integer())
    amount = db.Column(db.Numeric(12, 2))
    memo = db.Column(db.String())

    def __init__(self, transaction_id, account_id, amount, memo):
        # TODO: Docstring
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.amount = amount
        self.memo = memo


class Fingerprints(db.Model):
    # TODO: Docstring
    __tablename__ = 'fingerprints'
    userid = db.Column(db.Integer(), primary_key=True)
    fpdata = db.Column(db.LargeBinary())
    fpimg = db.Column(db.LargeBinary())

    def __init__(self, userid, fpdata, fpimg):
        # TODO: Docstring
        self.userid = userid
        self.fpdata = fpdata
        self.fpimg = fpimg


class FloorLocations(db.Model):
    # TODO: Docstring
    __tablename__ = 'floor_locations'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    markup = db.Column(db.Float())

    def __init__(self, id, name, markup):
        # TODO: Docstring
        self.id = id
        self.name = name
        self.markup = markup


class HistoricalPrices(db.Model):
    # TODO: Docstring
    __tablename__ = 'historical_prices'
    bulkid = db.Column(db.Integer())
    date = db.Column(db.Date())
    price = db.Column(db.Numeric(12, 2))
    id = db.Column(db.Integer(), primary_key=True)

    def __init__(self, bulkid, date, price):
        # TODO: Docstring
        self.bulkid = bulkid
        self.date = date
        self.price = price


class Inventory(db.Model):
    # TODO: Docstring
    __tablename__ = 'inventory'
    date = db.Column(db.Date(), primary_key=True)
    bulkid = db.Column(db.Integer(), primary_key=True)
    units = db.Column(db.Integer())
    cases = db.Column(db.Float())
    loose_units = db.Column(db.Integer())
    case_size = db.Column(db.Integer())

    def __init__(self, date, bulkid, units, cases, loose_units, case_size):
        # TODO: Docstring
        self.date = date
        self.bulkid = bulkid
        self.units = units
        self.cases = cases
        self.loose_units = loose_units
        self.case_size = case_size


class Messages(db.Model):
    # TODO: Docstring
    __tablename__ = 'messages'
    msgid = db.Column(db.Integer(), db.Sequence('msgid_seq'), primary_key=True)
    msgtime = db.Column(db.DateTime())
    userid = db.Column(db.Integer())
    message = db.Column(db.String())

    def __init__(self, msgtime, userid, message):
        # TODO: Docstring
        self.msgtime = msgtime
        self.userid = userid
        self.message = message


class OrderItems(db.Model):
    # TODO: Docstring
    __tablename__ = 'order_items'
    id = db.Column(db.Integer(), primary_key=True)
    order_id = db.Column(db.Integer())
    bulk_type_id = db.Column(db.Integer())
    quantity = db.Column(db.Integer())
    number = db.Column(db.Integer())
    case_cost = db.Column(db.Numeric(12, 2))
    crv_per_unit = db.Column(db.Numeric(12, 2))
    is_cost_taxed = db.Column(db.Boolean())
    is_crv_taxed = db.Column(db.Boolean())
    is_cost_migrated = db.Column(db.Boolean())

    def __init__(self, order_id, bulk_type_id, quantity, number, case_cost,
                 crv_per_unit, is_cost_taxed, is_crv_taxed, is_cost_migrated):
        # TODO: Docstring
        self.order_id = order_id
        self.bulk_type_id = bulk_type_id
        self.quantity = quantity
        self.number = number
        self.case_cost = case_cost
        self.crv_per_unit = crv_per_unit
        self.is_cost_taxed = is_cost_taxed
        self.is_crv_taxed = is_crv_taxed
        self.is_cost_migrated = is_cost_migrated


class Orders(db.Model):
    # TODO: Docstring
    __tablename__ = 'orders'
    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.Date())
    description = db.Column(db.String())
    amount = db.Column(db.Numeric(12, 2))
    tax_rate = db.Column(db.Numeric(6, 4))
    inventory_adjust = db.Column(db.Numeric(12, 2))
    supplies_adjust = db.Column(db.Numeric(12, 2))
    supplies_taxed = db.Column(db.Numeric(12, 2))
    supplies_nontaxed = db.Column(db.Numeric(12, 2))
    returns_taxed = db.Column(db.Numeric(12, 2))
    returns_nontaxed = db.Column(db.Numeric(12, 2))
    finance_transaction_id = db.Column(db.Integer())

    def __init__(self, date, description, amount, tax_rate, inventory_adjust,
                 supplies_adjust, supplies_taxed, supplies_nontaxed,
                 returns_taxed, returns_nontaxed, finance_transaction_id):
        # TODO: Docstring
        self.date = date
        self.description = description
        self.amount = amount
        self.tax_rate = tax_rate
        self.inventory_adjust = inventory_adjust
        self.supplies_adjust = supplies_adjust
        self.supplies_taxed = supplies_taxed
        self.supplies_nontaxed = supplies_nontaxed
        self.returns_taxed = returns_taxed
        self.returns_nontaxed = returns_nontaxed
        self.finance_transaction_id = finance_transaction_id


class ProductSource(db.Model):
    # TODO: Docstring
    __tablename__ = 'product_source'
    sourceid = db.Column(db.Integer(),
                         db.Sequence('product_source_sourceid_seq'),
                         primary_key=True)
    source_description = db.Column(db.String())

    # TODO (dbounov) product_source_sourceid_seq seems to be out of sync with
    # the values in the table. Once we fix this remove sourceid from
    # constructor arguments.
    def __init__(self, sourceid, source_description):
        # TODO: Docstring
        self.source_description = source_description
        self.sourceid = sourceid


class Products(db.Model):
    # TODO: Docstring
    __tablename__ = 'products'
    barcode = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String())
    phonetic_name = db.Column(db.String())
    price = db.Column(db.Numeric(12, 2))
    bulkid = db.Column(db.Integer())
    coffee = db.Column(db.Boolean())

    def __init__(self, barcode, name, phonetic_name, price, bulkid, coffee):
        # TODO: Docstring
        self.barcode = barcode
        self.name = name
        self.phonetic_name = phonetic_name
        self.price = price
        self.bulkid = bulkid
        self.coffee = coffee


class Profiles(db.Model):
    # TODO: Docstring
    __tablename__ = 'profiles'
    userid = db.Column(db.Integer(), primary_key=True)
    property = db.Column(db.String(), primary_key=True)
    setting = db.Column(db.Integer())

    def __init__(self, userid, property, setting):
        # TODO: Docstring
        self.userid = userid
        self.property = property
        self.setting = setting


class Roles(db.Model):
    # TODO: Docstring
    __tablename__ = 'roles'
    userid = db.Column(db.Integer(), primary_key=True)
    roles = db.Column(db.String())

    def __init__(self, userid, roles):
        # TODO: Docstring
        self.userid = userid
        self.roles = roles


class SodaInventory(db.Model):
    # TODO: Docstring
    __tablename__ = 'soda_inventory'
    slot = db.Column(db.String(), primary_key=True)
    count = db.Column(db.Integer())

    def __init__(self, slot, count):
        # TODO: Docstring
        assert(len(slot) <= 2)
        self.slot = slot
        self.count = count


class Transactions(db.Model):
    # TODO: Docstring
    __tablename__ = 'transactions'
    xacttime = db.Column(db.DateTime(True))
    userid = db.Column(db.Integer())
    xactvalue = db.Column(db.String())
    xacttype = db.Column(db.String())
    barcode = db.Column(db.String(), nullable=True)
    source = db.Column(db.String(), nullable=True)
    id = db.Column(db.Integer(), primary_key=True)
    finance_trans_id = db.Column(db.Integer(), nullable=True)

    def __init__(self, userid, xactvalue, xacttype, barcode, source,
                 finance_trans_id=None):
        # TODO: Docstring
        self.userid = userid
        self.xactvalue = xactvalue
        self.xacttype = xacttype
        self.barcode = barcode
        self.source = source
        self.finance_trans_id = finance_trans_id
        self.xacttime = datetime.datetime.now()


class UCSDEmails(db.Model):
    # TODO: Docstring
    __tablename__ = 'ucsd_emails'
    username = db.Column(db.String(), primary_key=True)

    def __init__(self, username):
        # TODO: Docstring
        self.username = username


class UserBarcodes(db.Model):
    # TODO: Docstring
    __tablename__ = 'userbarcodes'
    userid = db.Column(db.Integer())
    barcode = db.Column(db.String(), primary_key=True)

    def __init__(self, userid, barcode):
        # TODO: Docstring
        self.userid = userid
        self.barcode = barcode


class Users(db.Model):
    # TODO: Docstring
    __tablename__ = 'users'
    userid = db.Column(
        db.Integer(), db.Sequence('userid_seq'), primary_key=True)
    username = db.Column(db.String())
    email = db.Column(db.String())
    nickname = db.Column(db.String(), nullable=True)
    pwd = db.Column(db.String())
    balance = db.Column(db.Numeric(12, 2))
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
                 last_purchase_time, last_deposit_time, pref_auto_logout,
                 pref_speech, pref_forget_which_product,
                 pref_skip_purchase_confirm, notes, created_time, fraudulent):
        # TODO: Docstring
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
