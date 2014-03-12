#!/usr/bin/env python3.4

"""SodaServe, The ChezBob JSON-RPC Database Server.

Usage:
  soda_serve.py serve <dburl> [--config=<config-file>] [--address=<listen-address>] [--port=<port>] [--debug]
  soda_serve.py (-h | --help)
  soda_serve.py --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  --config=<config-file>        Use alternate config file. [default: config.json]
  --address=<listen-address>    Address to listen on. [default: 0.0.0.0]
  --port=<port>                 Port to listen on. [default: 8080]
  --debug                       Verbose debug output.

"""
from docopt import docopt

from flask import Flask, Response, jsonify
from flask_jsonrpc import JSONRPC
from flask_cors import cross_origin
from flask.ext.sqlalchemy import SQLAlchemy
from soda_session import SessionLocation, SessionManager, Session, User, users
import subprocess
import json
import soda_app
import os

app = soda_app.app
db = soda_app.db

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
         extras.append(to_jsonify_ready(products.query.filter(products.barcode==extra.barcode).first()))
    return extras

@jsonrpc.method('Bob.logout')
def bob_logout():
    sessionmanager.deregisterSession(SessionLocation.computer)
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
    with open(os.path.dirname(os.path.realpath(__file__)) + "/" +  arguments["--config"]) as json_data:
         configdata = json.load(json_data)
    if arguments['--debug']:
        print(arguments)
        app.config["SQLALCHEMY_RECORD_QUERIES"] = True
        app.config["SQLALCHEMY_ECHO"] = True
    if arguments['serve']:
        app.config["SQLALCHEMY_DATABASE_URI"] = arguments["<dburl>"]
        app.run(host=arguments['--address'], port=int(arguments['--port']), debug=arguments['--debug'],threaded=True)

