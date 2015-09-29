#!/usr/bin/env python3.4

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

# Flask application
app = Flask(__name__, static_url_path='/static')
db = SQLAlchemy(app)
