from flask import Flask, jsonify
from flask_jsonrpc import JSONRPC
from flask_cors import cross_origin
from flask.ext.sqlalchemy import SQLAlchemy

# Flask application
app = Flask(__name__)
db = SQLAlchemy(app)