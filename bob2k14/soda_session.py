#!/usr/bin/env python3.4

import datetime
import crypt
from enum import Enum
import soda_app
from sqlalchemy import func
from models import app, db, users, profiles, userbarcodes

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
            if location not in self.sessions or self.sessions[location] == None:
                self.sessions[location] = Session(user)
            elif not self.sessions[location].isvalid():
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
        if location not in self.sessions or self.sessions[location] == None:
            return False
        if not self.sessions[location].isvalid():
            return False
        return True

class Session:
    """Captures sessions"""
    def __init__(self, user):
        self.user = user
        self.triedsoda = 0
        self.logintime = datetime.datetime.now()
    def isvalid(self):
        return True
    def logout(self):
        return True

class User:
    """Authenticates users"""
    salt = "cB"
    def __init__(self):
        self.authenticated = False
        self.privacy = False
    def login_password(self, username, password):
        self.username = username
        user = users.query.filter(func.lower(users.username)==func.lower(username)).first()
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

