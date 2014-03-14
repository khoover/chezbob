from flask import Flask, jsonify
from flask_jsonrpc import JSONRPC
from flask_cors import cross_origin
from flask.ext.sqlalchemy import SQLAlchemy
import os
import queue
import requests
import json

# Flask application
app = Flask(__name__, static_url_path='/static')
db = SQLAlchemy(app)
arguments = []

event_subscriptions = []

class Subscription:
    """Manages subscriptions for event listening"""
    def __init__(self):
        self.queue = queue.Queue()

def add_subscription():
    subscription = Subscription()
    event_subscriptions.append(subscription)
    return subscription

def remove_subscription(subscription):
    event_subscriptions.remove(subscription)

def add_event(event):
    for subscriptions in event_subscriptions:
         subscriptions.queue.put(event)

@app.route('/static/js/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('js', path))

def make_jsonrpc_call(endpoint, call, args):
    print("making jsonrpc call")
    payload = {
                "method": call,
                "params": args ,
                "jsonrpc": "2.0",
                "id": 0
              }
    return requests.post(endpoint, data=json.dumps(payload), headers={'content-type': 'application/json'}).json()