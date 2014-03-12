import datetime
from enum import Enum

class SessionLocation(Enum):
    soda = 0
    computer = 1

class SessionManager:
    """Manages sessions"""
    def __init__(self):
        self.sessions = {}
    def registerSession(self, location, userid):
        if location not in self.sessions:
            self.sessions[location] = Session(userid)
        else:
            #is the previous session valid? if not, log the session out
            if self.sessions[location].isvalid():
                self.sessions[location].logout()
                self.sessions[location] = Sessions(userid)
            else:
                #session is valid, raise an exception
                raise Exception("User currently logged in")

class Session:
    """Captures sessions"""
    def __init__(self, userid):
        self.userid = userid
        self.logintime = datetime.datetime.now()
    def isvalid(self):
        return False
    def logout(self):
        return True

