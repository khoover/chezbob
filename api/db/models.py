#!/usr/bin/env python3.4

from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sqla;
Base = declarative_base()
from datetime import date, datetime

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


class AggregatePurchases(Base):

    # TODO: Docstring

    __tablename__ = 'aggregate_purchases'
    date = sqla.Column(sqla.Date(), primary_key=True)
    barcode = sqla.Column(sqla.String(), primary_key=True)
    quantity = sqla.Column(sqla.Integer())
    price = sqla.Column(sqla.Numeric(12, 2))
    bulkid = sqla.Column(sqla.Integer())

    def __init__(self, barcode, price, bulkid):
        # TODO: Docstring
        self.date = datetime.date.today()
        self.barcode = barcode
        self.quantity = 1
        self.price = price
        self.bulkid = bulkid


class BulkItems(Base):

    # TODO: Docstring

    __tablename__ = 'bulk_items'
    bulkid = sqla.Column(
        sqla.Integer(), sqla.Sequence('bulk_items_bulkid_seq'), primary_key=True)
    description = sqla.Column(sqla.String())
    price = sqla.Column(sqla.Numeric(12, 2))
    taxable = sqla.Column(sqla.Boolean())
    quantity = sqla.Column(sqla.Integer())
    updated = sqla.Column(sqla.Date())
    crv = sqla.Column(sqla.Numeric(12, 2))
    crv_taxable = sqla.Column(sqla.Boolean())
    source = sqla.Column(sqla.Integer())
    reserve = sqla.Column(sqla.Integer())
    active = sqla.Column(sqla.Boolean())
    floor_location = sqla.Column(sqla.Integer())
    product_id = sqla.Column(sqla.String())
    crv_per_unit = sqla.Column(sqla.Numeric(12, 2))
    bulkbarcode = sqla.Column(sqla.String())

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


class FinanceAccounts(Base):

    # TODO: Docstring

    __tablename__ = 'finance_accounts'
    id = sqla.Column(sqla.Integer(), sqla.Sequence(
        'finance_accounts_id_seq'), primary_key=True)
    type = sqla.Column(sqla.String())
    name = sqla.Column(sqla.String())

    def __init__(self, type, name):
        # TODO: Docstring
        assert(len(type) == 1)
        self.type = type
        self.name = name


class FinanceDepositSummary(Base):

    # TODO: Docstring

    __tablename__ = 'finance_deposit_summary'
    date = sqla.Column(sqla.Date(), primary_key=True)
    positive = sqla.Column(sqla.Integer())
    negative = sqla.Column(sqla.Integer())

    def __init__(self, date, positive, negative):
        # TODO: Docstring
        self.date = date
        self.positive = positive
        self.negative = negative


class FinanceInventorySummary(Base):

    # TODO: Docstring

    __tablename__ = 'finance_inventory_summary'
    date = sqla.Column(sqla.Date(), primary_key=True)
    value = sqla.Column(sqla.Integer())
    shrinkage = sqla.Column(sqla.Integer())

    def __init__(self, date, value, shrinkage):
        # TODO: Docstring
        self.date = date
        self.value = value
        self.shrinkage = shrinkage


class FinanceSplits(Base):
    # TODO: Docstring
    __tablename__ = 'finance_splits'
    id = sqla.Column(
        sqla.Integer(), sqla.Sequence('finance_splits_id_seq'), primary_key=True)
    transaction_id = sqla.Column(sqla.Integer())
    account_id = sqla.Column(sqla.Integer())
    amount = sqla.Column(sqla.Numeric(12, 2))
    memo = sqla.Column(sqla.String())

    def __init__(self, transaction_id, account_id, amount, memo):
        # TODO: Docstring
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.amount = amount
        self.memo = memo


class Fingerprints(Base):
    # TODO: Docstring
    __tablename__ = 'fingerprints'
    userid = sqla.Column(sqla.Integer(), primary_key=True)
    fpdata = sqla.Column(sqla.LargeBinary())
    fpimg = sqla.Column(sqla.LargeBinary())

    def __init__(self, userid, fpdata, fpimg):
        # TODO: Docstring
        self.userid = userid
        self.fpdata = fpdata
        self.fpimg = fpimg


class FloorLocations(Base):
    # TODO: Docstring
    __tablename__ = 'floor_locations'
    id = sqla.Column(sqla.Integer(), primary_key=True)
    name = sqla.Column(sqla.String())
    markup = sqla.Column(sqla.Float())

    def __init__(self, id, name, markup):
        # TODO: Docstring
        self.id = id
        self.name = name
        self.markup = markup


class HistoricalPrices(Base):
    # TODO: Docstring
    __tablename__ = 'historical_prices'
    bulkid = sqla.Column(sqla.Integer())
    date = sqla.Column(sqla.Date())
    price = sqla.Column(sqla.Numeric(12, 2))
    id = sqla.Column(sqla.Integer(), primary_key=True)

    def __init__(self, bulkid, date, price):
        # TODO: Docstring
        self.bulkid = bulkid
        self.date = date
        self.price = price


class Inventory(Base):
    # TODO: Docstring
    __tablename__ = 'inventory'
    date = sqla.Column(sqla.Date(), primary_key=True)
    bulkid = sqla.Column(sqla.Integer(), primary_key=True)
    units = sqla.Column(sqla.Integer())
    cases = sqla.Column(sqla.Float())
    loose_units = sqla.Column(sqla.Integer())
    case_size = sqla.Column(sqla.Integer())

    def __init__(self, date, bulkid, units, cases, loose_units, case_size):
        # TODO: Docstring
        self.date = date
        self.bulkid = bulkid
        self.units = units
        self.cases = cases
        self.loose_units = loose_units
        self.case_size = case_size


class Messages(Base):
    # TODO: Docstring
    __tablename__ = 'messages'
    msgid = sqla.Column(sqla.Integer(), sqla.Sequence('msgid_seq'), primary_key=True)
    msgtime = sqla.Column(sqla.DateTime())
    userid = sqla.Column(sqla.Integer())
    message = sqla.Column(sqla.String())

    def __init__(self, msgtime, userid, message):
        # TODO: Docstring
        self.msgtime = msgtime
        self.userid = userid
        self.message = message


class OrderItems(Base):
    # TODO: Docstring
    __tablename__ = 'order_items'
    id = sqla.Column(sqla.Integer(), primary_key=True)
    order_id = sqla.Column(sqla.Integer())
    bulk_type_id = sqla.Column(sqla.Integer())
    quantity = sqla.Column(sqla.Integer())
    number = sqla.Column(sqla.Integer())
    case_cost = sqla.Column(sqla.Numeric(12, 2))
    crv_per_unit = sqla.Column(sqla.Numeric(12, 2))
    is_cost_taxed = sqla.Column(sqla.Boolean())
    is_crv_taxed = sqla.Column(sqla.Boolean())
    is_cost_migrated = sqla.Column(sqla.Boolean())

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


class Orders(Base):
    # TODO: Docstring
    __tablename__ = 'orders'
    id = sqla.Column(sqla.Integer(), primary_key=True)
    date = sqla.Column(sqla.Date())
    description = sqla.Column(sqla.String())
    amount = sqla.Column(sqla.Numeric(12, 2))
    tax_rate = sqla.Column(sqla.Numeric(6, 4))
    inventory_adjust = sqla.Column(sqla.Numeric(12, 2))
    supplies_adjust = sqla.Column(sqla.Numeric(12, 2))
    supplies_taxed = sqla.Column(sqla.Numeric(12, 2))
    supplies_nontaxed = sqla.Column(sqla.Numeric(12, 2))
    returns_taxed = sqla.Column(sqla.Numeric(12, 2))
    returns_nontaxed = sqla.Column(sqla.Numeric(12, 2))
    finance_transaction_id = sqla.Column(sqla.Integer())

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


class ProductSource(Base):
    # TODO: Docstring
    __tablename__ = 'product_source'
    sourceid = sqla.Column(sqla.Integer(),
                         sqla.Sequence('product_source_sourceid_seq'),
                         primary_key=True)
    source_description = sqla.Column(sqla.String())

    # TODO (dbounov) product_source_sourceid_seq seems to be out of sync with
    # the values in the table. Once we fix this remove sourceid from
    # constructor arguments.
    def __init__(self, sourceid, source_description):
        # TODO: Docstring
        self.source_description = source_description
        self.sourceid = sourceid


class Products(Base):
    # TODO: Docstring
    __tablename__ = 'products'
    barcode = sqla.Column(sqla.String(), primary_key=True)
    name = sqla.Column(sqla.String())
    phonetic_name = sqla.Column(sqla.String())
    price = sqla.Column(sqla.Numeric(12, 2))
    bulkid = sqla.Column(sqla.Integer())
    coffee = sqla.Column(sqla.Boolean())

    def __init__(self, barcode, name, phonetic_name, price, bulkid, coffee):
        # TODO: Docstring
        self.barcode = barcode
        self.name = name
        self.phonetic_name = phonetic_name
        self.price = price
        self.bulkid = bulkid
        self.coffee = coffee


class Profiles(Base):
    # TODO: Docstring
    __tablename__ = 'profiles'
    userid = sqla.Column(sqla.Integer(), primary_key=True)
    property = sqla.Column(sqla.String(), primary_key=True)
    setting = sqla.Column(sqla.Integer())

    def __init__(self, userid, property, setting):
        # TODO: Docstring
        self.userid = userid
        self.property = property
        self.setting = setting


class Roles(Base):
    # TODO: Docstring
    __tablename__ = 'roles'
    userid = sqla.Column(sqla.Integer(), primary_key=True)
    roles = sqla.Column(sqla.String())

    def __init__(self, userid, roles):
        # TODO: Docstring
        self.userid = userid
        self.roles = roles


class SodaInventory(Base):
    # TODO: Docstring
    __tablename__ = 'soda_inventory'
    slot = sqla.Column(sqla.String(), primary_key=True)
    count = sqla.Column(sqla.Integer())

    def __init__(self, slot, count):
        # TODO: Docstring
        assert(len(slot) <= 2)
        self.slot = slot
        self.count = count


class Transactions(Base):
    # TODO: Docstring
    __tablename__ = 'transactions'
    xacttime = sqla.Column(sqla.DateTime(True))
    userid = sqla.Column(sqla.Integer())
    xactvalue = sqla.Column(sqla.String())
    xacttype = sqla.Column(sqla.String())
    barcode = sqla.Column(sqla.String(), nullable=True)
    source = sqla.Column(sqla.String(), nullable=True)
    id = sqla.Column(sqla.Integer(), primary_key=True)
    finance_trans_id = sqla.Column(sqla.Integer(), nullable=True)

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


class UCSDEmails(Base):
    # TODO: Docstring
    __tablename__ = 'ucsd_emails'
    username = sqla.Column(sqla.String(), primary_key=True)

    def __init__(self, username):
        # TODO: Docstring
        self.username = username


class UserBarcodes(Base):
    # TODO: Docstring
    __tablename__ = 'userbarcodes'
    userid = sqla.Column(sqla.Integer())
    barcode = sqla.Column(sqla.String(), primary_key=True)

    def __init__(self, userid, barcode):
        # TODO: Docstring
        self.userid = userid
        self.barcode = barcode


class Users(Base):
    # TODO: Docstring
    __tablename__ = 'users'
    userid = sqla.Column(
        sqla.Integer(), sqla.Sequence('userid_seq'), primary_key=True)
    username = sqla.Column(sqla.String())
    email = sqla.Column(sqla.String())
    nickname = sqla.Column(sqla.String(), nullable=True)
    pwd = sqla.Column(sqla.String())
    balance = sqla.Column(sqla.Numeric(12, 2))
    disabled = sqla.Column(sqla.Boolean())
    last_purchase_time = sqla.Column(sqla.DateTime(True))
    last_deposit_time = sqla.Column(sqla.DateTime(True))
    pref_auto_logout = sqla.Column(sqla.Boolean())
    pref_speech = sqla.Column(sqla.Boolean())
    pref_forget_which_product = sqla.Column(sqla.Boolean())
    pref_skip_purchase_confirm = sqla.Column(sqla.Boolean())
    notes = sqla.Column(sqla.String())
    created_time = sqla.Column(sqla.DateTime())
    fraudulent = sqla.Column(sqla.Boolean())

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
