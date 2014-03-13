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
            if self.sessions[location] is None:
                self.sessions[location] = Session(user)
            if not self.sessions[location].isvalid():
                self.sessions[location].logout()
                self.sessions[location] = Session(user)
            else:
                #session is valid, raise an exception
                raise Exception("User currently logged in")
        if location == SessionLocation.computer:
             soda_app.add_event("login")
        elif location == SessionLocation.soda:
             soda_app.add_event("slogin")
    def deregisterSession(self, location):
        self.sessions[location] = None
        if location == SessionLocation.computer:
             soda_app.add_event("logout")
        elif location == SessionLocation.soda:
             soda_app.add_event("slogout")
    def checkSession(self, location):
        if self.sessions[location] is None:
            return False
        if not self.sessions[location].isvalid():
            return False
        return True

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
  nickname = db.Column(db.String(), nullable = True)
  pwd = db.Column(db.String())
  balance = db.Column(db.Numeric(12,2))
  disabled = db.Column(db.Boolean())
  last_purchase_time = db.Column(db.DateTime(True))
  last_deposit_time = db.Column(db.DateTime(True))
  pref_auto_logout = db.Column(db.Boolean())
  pref_speech = db.Column(db.Boolean())
  pref_forget_which_product = db.Column(db.Boolean())
  pref_skip_purchase_confirm = db.Column(db.Boolean())
  notes = db.Column(db.String())
  created_time = db.Column(db.DateTime())
  fraudulent = db.Column(db.Boolean())

"""
                      Table "public.profiles"
  Column  |       Type        | Modifiers | Storage  | Description 
----------+-------------------+-----------+----------+-------------
 userid   | integer           | not null  | plain    | 
 property | character varying | not null  | extended | 
 setting  | integer           | not null  | plain    | 
"""

class profiles(db.Model):
  __tablename__ = 'profiles'
  userid = db.Column(db.Integer(), primary_key = True)
  property = db.Column(db.String(), primary_key = True)
  setting = db.Column(db.Integer())

"""
              Table "public.userbarcodes"
 Column  |  Type   | Modifiers | Storage  | Description 
---------+---------+-----------+----------+-------------
 userid  | integer | not null  | plain    | 
 barcode | text    | not null  | extended | 
"""

class userbarcodes(db.Model):
  __tablename__ = 'userbarcodes'
  userid = db.Column(db.Integer())
  barcode = db.Column(db.String(), primary_key = True)
  
class User:
    """Authenticates users"""
    salt = "cB"
    def __init__(self):
        self.authenticated = False
        self.privacy = False
    def login_password(self, username, password):
        self.username = username
        user = users.query.filter(users.username==username).first()
        if user is not None:
             if user.pwd == None or user.pwd == "" or password == user.pwd:
                   self.user = user
                   self.authenticated = True
                   self.privacy = False
                   privacy = profiles.query.filter(profiles.userid==user.userid).filter(profiles.property=="privacy").first()
                   if privacy is not None:
                          if privacy.setting == 1:
                               self.privacy = True
                   return True
             else:
                   raise Exception("Authentication Failure")
        raise Exception("Nonexistent User")
    def login_barcode(self, barcode):
        userbarcode = userbarcodes.query.filter(userbarcodes.barcode==barcode).first()
        if userbarcode is not None:
             userid = userbarcode.userid
             self.user = users.query.filter(users.userid == userid).first()
             self.authenticated = True
             privacy = profiles.query.filter(profiles.userid==userid).filter(profiles.property=="privacy").first()
             if privacy is not None:
                  if privacy.setting == 1:
                       self.privacy = True
             return True
        else:
             raise Exception("Authentication Failure")
    def logout(self):
        return True

