#!/usr/bin/env python3.4

"""SodaServe, The ChezBob JSON-RPC Database Server.

Usage:
  soda_serve.py serve <dburl> [--config=<config-file>] [--mdb-server-ep=<ep>] [--vdb-server-ep=<ep>] [--address=<listen-address>] [--port=<port>] [--debug]
  soda_serve.py (-h | --help)
  soda_serve.py --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  --config=<config-file>        Use alternate config file. [default: config.json]
  --address=<listen-address>    Address to listen on. [default: 0.0.0.0]
  --port=<port>                 Port to listen on. [default: 8080]
  --mdb-server-ep=<ep>          Endpoint of MDB server. [default: http://127.0.0.1:8081/api]
  --vdb-server-ep=<ep>          Endpoint of VDB server. [default: http://127.0.0.1:8083/api]
  --debug                       Verbose debug output.

"""
from docopt import docopt

from flask import Flask, Response, jsonify
from flask_jsonrpc import JSONRPC
from flask_cors import cross_origin
from flask.ext.sqlalchemy import SQLAlchemy

from soda_session import SessionLocation, SessionManager, Session, User
import subprocess
import json
import soda_app
import os
import datetime
import requests
import sys
from models import app, db, aggregate_purchases, products, transactions, users
from decimal import *
from enum import Enum

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

def make_purchase(user, product, location, privacy=False):
    # Get the purchase price of the item
    value = product.price
    # Deduct the balance from the user's account
    user.balance -= value
    # Insert into the aggregate_purchases table
    aggregate = aggregate_purchases(product.barcode, value, product.bulkid)
    # Insert into the transaction table, respecting the user's privacy settings
    barcode = product.barcode
    description = "BUY " + product.name.upper()
    if privacy:
        description = "BUY"
        barcode = ""
    transact = transactions(userid=user.userid, xactvalue=-value, xacttype=description, barcode=barcode, source=location)
    # Commit our changes
    db.session.add(aggregate)
    db.session.add(transact)
    db.session.merge(user)
    db.session.commit()
    return True

def make_purchase_other(user, value, location):
    # fail if the price doesn't make sense
    # TODO: do we really want abs(value) here?
    if (value < 0):
        return False
    # update the balance
    user.balance -= value
    print ("deducted value")
    # now create a matching record in transactions
    transact = transactions(userid=user.userid, xactvalue=-value, xacttype="BUY OTHER", barcode=None, source="chezbob2k14")
    print ("made transaction")
    # commit our changes
    db.session.add(transact)
    db.session.merge(user)
    db.session.commit()
    print ("merged")
    return True

def make_deposit(user, amount, location):
    # update the user's balance
    user.balance += amount
    # make a matching record in transactions
    transact = transactions(userid=user.userid, xactvalue=amount, xacttype="ADD", barcode=None, source=location)
    # commit our changes
    db.session.add(transact)
    db.session.merge(user)
    db.session.commit()
    return True

def adduserbarcode(userid, barcode):
    # Technically, this only makes sense if the user is logged in.
    # No other function seems to be checking, though, so...

    #if not sessionmanager.checkSession(SessionLocation.computer):
    #    return False
    # -- OR --
    #if userid is None:
    #    return False

    barcode = barcode.strip(' "')
    print("Attempting to add user barcode ", barcode)
    ubc = userbarcodes.query.filter(userbarcodes.barcode==barcode).first()

    if ubc is None:
        # We didn't find a barcode like that one, so we can create a new one.
        ubc = userbarcodes(userid=userid, barcode=barcode)
        print("...barcode is available")

        db.session.merge(ubc)
        db.session.commit()
    elif ubc.userid != userid:
        # We found this barcode in use by another user
        print("...barcode in use")
        sys.stdout.flush()
        raise Exception("Barcode in use")

    # Implicitly, we may have already found that barcode in use.
    # In which case, we succeed by default.

    return True

@jsonrpc.method('Soda.remotebarcode')
def remotebarcode(type, barcode):
    #several things to check here. first, if there is anyone logged in, we're probably buying something, so check that.
    if sessionmanager.checkSession(SessionLocation.soda):
         # Get the user, product, location, and privacy settings
         user = sessionmanager.sessions[SessionLocation.soda].user.user
         product = products.query.filter(products.barcode==barcode).first()
         location = "soda"
         privacy = sessionmanager.sessions[SessionLocation.soda].user.privacy
         # make a purchase, which also updates the db
         make_purchase(user, product, location, privacy)
         soda_app.add_event("sbc" + barcode)
    else:
         #do a login
         user = User()
         user.login_barcode(barcode)
         #logout any existing session
         sessionmanager.deregisterSession(SessionLocation.soda)
         sessionmanager.registerSession(SessionLocation.soda, user)
    return ""

#this should be safe since only one can can be vended at once...
lastsoda = ""
@jsonrpc.method('Soda.remotevdb')
def remotevdb(event):
    if event[0:1] == "R":
        #someone is trying to buy a soda. if no one is logged in, tell them guest mode isn't ready.
         if sessionmanager.checkSession(SessionLocation.soda):
              soda_app.add_event("vdr" + configdata["sodamapping"][event[9:12]])
              result = soda_app.make_jsonrpc_call(soda_app.arguments["--vdb-server-ep"], "Vdb.command", ["A"])
              lastsoda = event[9:12]
         else:
              soda_app.add_event("vdd")
              result = soda_app.make_jsonrpc_call(soda_app.arguments["--vdb-server-ep"], "Vdb.command", ["D"])
    elif event[0:1] == "L":
        #vend failed, don't charge
        soda_app.add_event("vdf")
        result = soda_app.make_jsonrpc_call(soda_app.arguments["--vdb-server-ep"], "Vdb.command", ["X"])
    elif event[0:1] == "K":
        #vend success
        remotebarcode("R", configdata["sodamapping"][event[9:12]])
        result = soda_app.make_jsonrpc_call(soda_app.arguments["--vdb-server-ep"], "Vdb.command", ["X"])
    elif event[0:1] == "M":
        #vend success
        if sessionmanager.checkSession(SessionLocation.soda):
            result = soda_app.make_jsonrpc_call(soda_app.arguments["--vdb-server-ep"], "Vdb.command", ["C"])
        else:
            result = soda_app.make_jsonrpc_call(soda_app.arguments["--vdb-server-ep"], "Vdb.command", ["X"])

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
         make_deposit(user, amount, "soda")
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
              #now credit to the user
              user = sessionmanager.sessions[SessionLocation.soda].user.user
              make_deposit(user, amount, "soda")
         soda_app.add_event("dec" + str(amount))
    elif event [0:1] == "W":
         #logout
         #get rid of bills in escrow (guessing this is what people expect)
         result = soda_app.make_jsonrpc_call(soda_app.arguments["--mdb-server-ep"], "Mdb.command", ["K2"])
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

@jsonrpc.method('Bob.adduserbarcode')
def bob_adduserbarcode(barcode):
    userid = sessionmanager.sessions[SessionLocation.computer].user.user.userid
    return adduserbarcode(userid, barcode)

@jsonrpc.method('Bob.getuserbarcode')
def bob_getuserbarcode(barcode):
    userid = sessionmanager.sessions[SessionLocation.computer].user.user.userid

    ubc = userbarcodes.query.filter(userbarcodes.userid==userid).first()
    if ubc is None:
        return ""
    return ubc.barcode

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
def bob_getbalance():
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

@jsonrpc.method('Bob.sendmessage')
def bob_sendmessage(message, anonymous):
    username = sessionmanager.sessions[SessionLocation.computer].user.user.username
    if (anonymous == "1"):
        username = "anonymous"
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "New ChezBob E-Mail from User"
    msg['From'] = "chezbob@cs.ucsd.edu"
    msg['Cc'] = sessionmanager.sessions[SessionLocation.computer].user.user.email
    msg['To'] = "chezbob@cs.ucsd.edu"
    htmlout = """
        <html>
            <head></head>
            <body>
                Hello,<br/>
                      <br/>
                      The user {0} (email: {1}) sent a message to ChezBob via the ChezBob interface. The message reads:<br/>
                    <br/>
                    {2}
                    <br/>
                    -eom-
            </body>
        </html>
    """.format(username, msg['Cc'], message)
    plainout = """
Hello,

The user {0} (email: {1}) sent a message to ChezBob via the ChezBob interface. The message reads:

{2}

-eom-
    """.format(username, msg['Cc'], message)
    msg.attach(MIMEText(htmlout, 'html'))
    msg.attach(MIMEText(plainout, 'plain'))
    s = smtplib.SMTP('localhost')
    s.sendmail(msg['From'], msg['To'] + "," + msg['Cc'], msg.as_string())
    s.quit()

@jsonrpc.method('Bob.getbarcodeinfo')
def bob_getbarcodeinfo(barcode):
    return to_jsonify_ready(products.query.filter(products.barcode==barcode).first())

@jsonrpc.method('Bob.purchasebarcode')
def bob_purchasebarcode(barcode):
    #ok, we're supposed to subtract the balance from the user first,
    user = sessionmanager.sessions[SessionLocation.computer].user.user
    product = products.query.filter(products.barcode==barcode).first()
    location = "chezbob2k14"
    privacy = sessionmanager.sessions[SessionLocation.computer].user.privacy
    return make_purchase(user, product, location, privacy)

@jsonrpc.method('Bob.purchaseother')
def bob_purchaseother(amount):
    #ok, we're supposed to subtract the balance from the user first,
    user = sessionmanager.sessions[SessionLocation.computer].user.user
    value = Decimal(amount.strip(' "'))
    return make_purchase_other(user, value, "chezbob2k14")

@jsonrpc.method('Bob.deposit')
def bob_deposit(amount):
    #ok, we're supposed to subtract the balance from the user first,
    value = Decimal(amount.strip(' "'))
    user = sessionmanager.sessions[SessionLocation.computer].user.user
    return make_deposit(user, value, "chezbob2k14")

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

