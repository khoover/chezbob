#!/usr/bin/env python3.4

"""SodaServe, The ChezBob JSON-RPC Database Server.

Usage:
  soda_serve.py serve <dburl> [--config=<config-file>] [--mdb-server-ep=<ep>] [--address=<listen-address>] [--port=<port>] [--debug]
  soda_serve.py (-h | --help)
  soda_serve.py --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  --config=<config-file>        Use alternate config file. [default: config.json]
  --address=<listen-address>    Address to listen on. [default: 0.0.0.0]
  --port=<port>                 Port to listen on. [default: 8080]
  --mdb-server-ep=<ep>          Endpoint of MDB server. [default: http://127.0.0.1:8081/api]
  --debug                       Verbose debug output.

"""
from docopt import docopt

from flask import Flask, Response, jsonify
from flask_jsonrpc import JSONRPC
from flask_cors import cross_origin
from flask.ext.sqlalchemy import SQLAlchemy
from soda_session import SessionLocation, SessionManager, Session, User, users
from decimal import Decimal
import subprocess
import json
import soda_app
import os
import datetime
import requests
from decimal import *
from enum import Enum

app = soda_app.app
db = soda_app.db

class vmcstates(Enum):
    reset = 0
    enabled = 1
    vsession = 2
    vsessionidle =3
    configured = 4
    vapproved = 5
    vdeny = 6
    vsessionend = 7
    disabled = 8
    cancel = 9

def get_git_revision_hash():
    return str(subprocess.check_output(['git', 'rev-parse', 'HEAD', '--work-tree=/git' ,'--git-dir=/git']))

def to_jsonify_ready(model):
    """ Returns a JSON representation of an SQLAlchemy-backed object.
    """
    json = {}
    if model != None:
        for col in model._sa_class_manager.mapper.mapped_table.columns:
            json[col.name] = str(getattr(model, col.name))

    return json

#db models - todo: move this into models.py or similar

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

# Flask-JSONRPC
jsonrpc = JSONRPC(app, '/api', enable_web_browsable_api=True)

@jsonrpc.method('Soda.index')
@cross_origin()
def json_index():
    return 'SodaServe ' + get_git_revision_hash()

@jsonrpc.method('Soda.products')
@cross_origin()
def product(barcode):
    return to_jsonify_ready(products.query.filter(products.barcode==barcode).first())

@jsonrpc.method('Soda.remotebarcode')
def remotebarcode(type, barcode):
    #several things to check here. first, if there is anyone logged in, we're probably buying something, so check that.
    if sessionmanager.checkSession(SessionLocation.soda):
         #do a purchase
         #ok, we're supposed to subtract the balance from the user first,
         product = products.query.filter(products.barcode==barcode).first()
         value = product.price
         user = sessionmanager.sessions[SessionLocation.soda].user.user
         user.balance -= value
         description = "BUY " + product.name.upper()
         barcode = product.barcode
         if sessionmanager.sessions[SessionLocation.soda].user.privacy:
              description = "BUY"
              barcode = ""
         #now create a matching record in transactions
         transact = transactions(userid=user.userid, xactvalue=-value, xacttype=description, barcode=barcode, source="soda")
         db.session.add(transact)
         db.session.merge(user)
         db.session.commit()
         soda_app.add_event("sbc" + barcode)
    else:
         #do a login
         user = User()
         user.login_barcode(barcode)
         #logout any existing session
         sessionmanager.deregisterSession(SessionLocation.soda)
         sessionmanager.registerSession(SessionLocation.soda, user)
    return ""

@jsonrpc.method('Soda.remotemdb')
def remotemdb(event):
     #let's make sure theres a user logged in. if not, just tell them that guest mode isn't ready yet.
    if event[0:2] == "Q1":
         if sessionmanager.checkSession(SessionLocation.soda):
              result = soda_app.make_jsonrpc_call(soda_app.arguments["--mdb-server-ep"], "Mdb.command", ["K1"])
         else:
              result = soda_app.make_jsonrpc_call(soda_app.arguments["--mdb-server-ep"], "Mdb.command", ["K2"])
    elif event [0:2] == "Q2":
         #well, someone better be logged in. the bill was stacked.
         billtype = event[3:5]
         amount = 0
         if billtype == "00":
              amount = 1
         elif billtype == "01":
              amount = 5
         elif billtype == "02":
              amount = 10
         elif billtype == "03":
              amount = 20
         elif billtype == "04":
              amount = 50
         elif billtype == "05":
              amount = 100
         #now credit to the user.
         user = sessionmanager.sessions[SessionLocation.soda].user.user
         user.balance += amount
         description = "ADD "
         barcode = None
         #now create a matching record in transactions
         transact = transactions(userid=user.userid, xactvalue=+amount, xacttype=description, barcode=barcode, source="soda")
         db.session.add(transact)
         db.session.merge(user)
         db.session.commit()
         soda_app.add_event("deb" + str(amount))
    elif event [0:2] == "P1":
         if not sessionmanager.checkSession(SessionLocation.soda):
              #refund it since we're not logged in.
              result = soda_app.make_jsonrpc_call(soda_app.arguments["--mdb-server-ep"], "Mdb.command", ["G " + event[3:5] + " 01"])
         else:
              #coins!
              cointype = event[3:5]
              amount = 0
              if cointype == "00":
                   amount = 0.5
              elif cointype == "01":
                   amount = 0.10
              elif cointype == "02":
                   amount = 0.25
              #now credit to the user.
              user = sessionmanager.sessions[SessionLocation.soda].user.user
              user.balance += Decimal(amount)
              description = "ADD "
              barcode = None
              #now create a matching record in transactions
              transact = transactions(userid=user.userid, xactvalue=+amount, xacttype=description, barcode=barcode, source="soda")
              db.session.add(transact)
              db.session.merge(user)
              db.session.commit()
         soda_app.add_event("dec" + str(amount))
    elif event [0:1] == "W":
         #logout
         sessionmanager.deregisterSession(SessionLocation.soda)
    return ""

@jsonrpc.method('Soda.getusername')
def soda_getusername():
    if sessionmanager.sessions[SessionLocation.soda].user.user.nickname == None:
         return sessionmanager.sessions[SessionLocation.soda].user.user.username
    else:
         return sessionmanager.sessions[SessionLocation.soda].user.user.nickname

@jsonrpc.method('Soda.getbalance')
def soda_getbalance():
    #force the balance to update
    userid = sessionmanager.sessions[SessionLocation.soda].user.user.userid
    user = users.query.filter(users.userid == userid).first()
    return str(user.balance)

@jsonrpc.method('Soda.passwordlogin')
def soda_passwordlogin(username, password):
    user = User()
    user.login_password(username,password)
    #logout any existing session
    sessionmanager.deregisterSession(SessionLocation.soda)
    sessionmanager.registerSession(SessionLocation.soda, user)
    return to_jsonify_ready(sessionmanager.sessions[SessionLocation.soda].user.user)

@jsonrpc.method('Soda.logout')
def bob_logout():
    sessionmanager.deregisterSession(SessionLocation.soda)
    return ""

#bob tasks
@jsonrpc.method('Bob.index')
def bob_json_index():
    return 'SodaServe (Bob) ' + get_git_revision_hash()

@jsonrpc.method('Bob.passwordlogin')
def bob_passwordlogin(username, password):
    user = User()
    user.login_password(username,password)
    #logout any existing session
    sessionmanager.deregisterSession(SessionLocation.computer)
    sessionmanager.registerSession(SessionLocation.computer, user)
    return to_jsonify_ready(sessionmanager.sessions[SessionLocation.computer].user.user)

@jsonrpc.method('Bob.barcodelogin')
def bob_barcodelogin(barcode):
    user = User()
    user.login_barcode(barcode)
    #logout any existing session
    sessionmanager.deregisterSession(SessionLocation.computer)
    sessionmanager.registerSession(SessionLocation.computer, user)
    return to_jsonify_ready(sessionmanager.sessions[SessionLocation.computer].user.user)

@jsonrpc.method('Bob.getusername')
def bob_getusername():
    if sessionmanager.sessions[SessionLocation.computer].user.user.nickname == None:
         return sessionmanager.sessions[SessionLocation.computer].user.user.username
    else:
         return sessionmanager.sessions[SessionLocation.computer].user.user.nickname

@jsonrpc.method('Bob.getbalance')
def bob_getusername():
    return str(sessionmanager.sessions[SessionLocation.computer].user.user.balance)

@jsonrpc.method('Bob.sodalogin')
def bob_sodalogin():
    sessionmanager.registerSession(SessionLocation.soda, sessionmanager.sessions[SessionLocation.computer].user)
    sessionmanager.deregisterSession(SessionLocation.computer)
    return to_jsonify_ready(sessionmanager.sessions[SessionLocation.soda].user.user)

@jsonrpc.method('Bob.getcrypt')
def bob_getcrypt(username):
    return users.query.filter(users.username==username).first().pwd

@jsonrpc.method('Bob.getextras')
def bob_getextras():
    extras = []
    for extra in configdata["extraitems"]:
         extras.append(to_jsonify_ready(products.query.filter(products.barcode==extra["barcode"]).first()))
    return extras

@jsonrpc.method('Bob.getbarcodeinfo')
def bob_getbarcodeinfo(barcode):
    return to_jsonify_ready(products.query.filter(products.barcode==barcode).first())

@jsonrpc.method('Bob.purchasebarcode')
def bob_purchasebarcode(barcode):
    #ok, we're supposed to subtract the balance from the user first,
    product = products.query.filter(products.barcode==barcode).first()
    value = product.price
    user = sessionmanager.sessions[SessionLocation.computer].user.user
    user.balance -= value
    description = "BUY " + product.name.upper()
    barcode = product.barcode
    if sessionmanager.sessions[SessionLocation.computer].user.privacy:
         description = "BUY"
         barcode = ""
    #now create a matching record in transactions
    transact = transactions(userid=user.userid, xactvalue=-value, xacttype=description, barcode=barcode, source="chezbob2k14")
    db.session.add(transact)
    db.session.merge(user)
    db.session.commit()
    return True

@jsonrpc.method('Bob.purchaseother')
def bob_purchaseother(amount):
    #ok, we're supposed to subtract the balance from the user first,
    value = Decimal(amount.strip(' "'))
    user = sessionmanager.sessions[SessionLocation.computer].user.user
    user.balance -= value
    description = "BUY OTHER"
    barcode = None
    if (value < 0):
    #now create a matching record in transactions
    transact = transactions(userid=user.userid, xactvalue=-value, xacttype=description, barcode=barcode, source="chezbob2k14")
    db.session.add(transact)
    db.session.merge(user)
    db.session.commit()
    return True

@jsonrpc.method('Bob.deposit')
def bob_purchaseother(amount):
    #ok, we're supposed to subtract the balance from the user first,
    value = Decimal(amount.strip(' "'))
    user = sessionmanager.sessions[SessionLocation.computer].user.user
    user.balance += value
    description = "ADD"
    barcode = None
    #now create a matching record in transactions
    transact = transactions(userid=user.userid, xactvalue=value, xacttype=description, barcode=barcode, source="chezbob2k14")
    db.session.add(transact)
    db.session.merge(user)
    db.session.commit()
    return True

@jsonrpc.method('Bob.transactions')
def bob_transactions():
    userid = sessionmanager.sessions[SessionLocation.computer].user.user.userid
    query = transactions.query.filter(transactions.userid==userid).order_by(transactions.xacttime.desc()).limit(10)
    results = []
    for q in query:
         results.append(to_jsonify_ready(q))
    return results

@jsonrpc.method('Bob.logout')
def bob_logout():
    sessionmanager.deregisterSession(SessionLocation.computer)
    return ""

@jsonrpc.method('Util.force_refresh')
def util_force_refresh():
    soda_app.add_event("refresh")
    return ""

@app.route("/")
def index():
     return jsonify(to_jsonify_ready(products.query.first()))

def event_stream():
    subscription = soda_app.add_subscription()
    try:
         while True:
              result = subscription.queue.get()
              yield 'data: %s\n\n' % str(result)
    except GeneratorExit as ge:
         soda_app.remove_subscription(subscription)

@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype="text/event-stream")


sessionmanager = SessionManager()
configdata = []

if __name__ == '__main__':
    arguments = docopt(__doc__, version='SodaServe 1.0')
    soda_app.arguments = arguments
    with open(os.path.dirname(os.path.realpath(__file__)) + "/" +  arguments["--config"]) as json_data:
         configdata = json.load(json_data)
    if arguments['--debug']:
        print(arguments)
        app.config["SQLALCHEMY_RECORD_QUERIES"] = True
        app.config["SQLALCHEMY_ECHO"] = True
    if arguments['serve']:
        app.config["SQLALCHEMY_DATABASE_URI"] = arguments["<dburl>"]
        app.run(host=arguments['--address'], port=int(arguments['--port']), debug=arguments['--debug'],threaded=True)

