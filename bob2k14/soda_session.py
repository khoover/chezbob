import datetime
import crypt
from enum import Enum
import soda_app

app = soda_app.app
db = soda_app.db


class SessionLocation(Enum):
    soda = 0
    computer = 1

class SessionManager:
    """Manages sessions"""
    def __init__(self):
        self.sessions = {}
    def registerSession(self, location, user):
        if location not in self.sessions:
            self.sessions[location] = Session(user)
        else:
            #is the previous session valid? if not, log the session out
            if self.sessions[location].isvalid():
                self.sessions[location].logout()
                self.sessions[location] = Sessions(userid)
            else:
                #session is valid, raise an exception
                raise Exception("User currently logged in")
        soda_app.event_queue.put("login")

class Session:
    """Captures sessions"""
    def __init__(self, user):
        self.user = user
        self.logintime = datetime.datetime.now()
    def isvalid(self):
        return False
    def logout(self):
        return True
"""
                                             Table "public.users"
           Column           |            Type             |         Modifiers         | Storage  | Description 
----------------------------+-----------------------------+---------------------------+----------+-------------
 userid                     | integer                     | not null                  | plain    | 
 username                   | character varying           | not null                  | extended | 
 email                      | character varying           | not null                  | extended | 
 nickname                   | character varying           |                           | extended | 
 pwd                        | text                        |                           | extended | 
 balance                    | numeric(12,2)               | not null default 0.00     | main     | 
 disabled                   | boolean                     | not null default false    | plain    | 
 last_purchase_time         | timestamp with time zone    |                           | plain    | 
 last_deposit_time          | timestamp with time zone    |                           | plain    | 
 pref_auto_logout           | boolean                     | not null default false    | plain    | 
 pref_speech                | boolean                     | not null default false    | plain    | 
 pref_forget_which_product  | boolean                     | not null default false    | plain    | 
 pref_skip_purchase_confirm | boolean                     | not null default false    | plain    | 
 notes                      | text                        | not null default ''::text | extended | 
 created_time               | timestamp without time zone | default now()             | plain    | 
 fraudulent                 | boolean                     | not null default false    | plain    | 
"""

class users(db.Model):
  __tablename__ = 'users'
  userid = db.Column(db.Integer(), primary_key = True)
  username = db.Column(db.String())
  email = db.Column(db.String())
  nickname = db.Column(db.String())
  pwd = db.Column(db.String())
  balance = db.Column(db.Numeric(12,2))
  disabled = db.Column(db.Boolean())
  last_purchase_time = db.Column(db.DateTime())
  last_deposit_time = db.Column(db.DateTime())
  pref_auto_logout = db.Column(db.Boolean())
  pref_speech = db.Column(db.Boolean())
  pref_forget_which_product = db.Column(db.Boolean())
  pref_skip_purchase_confirm = db.Column(db.Boolean())
  notes = db.Column(db.String())
  created_time = db.Column(db.DateTime())
  fraudulent = db.Column(db.Boolean())

class User:
    """Authenticates users"""
    salt = "cB"
    def __init__(self):
        self.authenticated = False
    def login_password(self, username, password):
        self.username = username
        user = users.query.filter(users.username==username).first()
        if user is not None:
             if password == user.pwd:
                   self.user = user
                   self.authenticated = True
                   return True
             else:
                   raise Exception("Authentication Failure")
        raise Exception("Nonexistent User")
    def logout(self):
        return True

