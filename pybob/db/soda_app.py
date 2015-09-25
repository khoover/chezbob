#!/usr/bin/env python3.4

from flask import Flask, jsonify
from flask_jsonrpc import JSONRPC
from flask_cors import cross_origin
from flask.ext.sqlalchemy import SQLAlchemy
import os
import queue
import logging
import requests
import sys
import json

# Flask application
app = Flask(__name__, static_url_path='/static')
db = SQLAlchemy(app)
