#!/usr/bin/env python3.4

"""SodaServe, The ChezBob JSON-RPC Database Server.

Usage:
  soda-serve.py serve <dburl> [--address=<listen-address>] [--port=<port>] [--debug]
  sdoa-serve.py (-h | --help)
  soda-serve.py --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  --address=<listen-address>    Address to listen on. [default: 0.0.0.0]
  --port=<port>                 Port to listen on. [default: 8080]
  --debug                       Verbose debug output.

"""
from docopt import docopt

from flask import Flask, jsonify
from flask_jsonrpc import JSONRPC
from flask_cors import cross_origin
from flask.ext.sqlalchemy import SQLAlchemy

def to_jsonify_ready(model):
    """ Returns a JSON representation of an SQLAlchemy-backed object.
    """
    json = {}
    if model != None:
        for col in model._sa_class_manager.mapper.mapped_table.columns:
            json[col.name] = str(getattr(model, col.name))

    return json

# Flask application
app = Flask(__name__)
db = SQLAlchemy(app)

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
jsonrpc = JSONRPC(app, '/api')

@jsonrpc.method('Soda.index')
def json_index():
    return 'SodaServe 1.0'

@jsonrpc.method('Soda.products')
def product(barcode):
    return to_jsonify_ready(products.query.filter(products.barcode==barcode).first())

@app.route("/")
@cross_origin()
def index():
     return jsonify(to_jsonify_ready(products.query.first()))

if __name__ == '__main__':
    arguments = docopt(__doc__, version='SodaServe 1.0')
    if arguments['--debug']:
        print(arguments)
        app.config["SQLALCHEMY_RECORD_QUERIES"] = True
        app.config["SQLALCHEMY_ECHO"] = True
    if arguments['serve']:
        app.config["SQLALCHEMY_DATABASE_URI"] = arguments["<dburl>"]
        app.run(host=arguments['--address'], port=int(arguments['--port']), debug=arguments['--debug'])

