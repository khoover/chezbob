import socket
import select
import os
import sys
import threading
import random

# XXX We don't check env vars for addr/port

def genTag():
    return str(random.randint(0,1<<32))

def echo_handler(data):
    print "E~" + " | ".join(data)
    return 0

def noop_handler(data):
    return 0

class ServIO:
    '''ServIO Python Class.  Currently overly lightweight'''
    def __init__(self, appname="PyServIO", appversion="0.0"):
        self.port = 2732 #SODACTRL_PORT=2732
        self.s = socket.socket(
                               socket.AF_INET,
                               socket.SOCK_STREAM,
                              )
        self.s.connect(("127.0.0.1", self.port))
        print self.s.getsockname()

        self.s.setblocking(0)
        self.default_handler = echo_handler

        self.handler_table = {}
        self.watchMessage("SYS-NOTWELCOME", self._abort_handler)
        self.watchMessage("SYS-WELCOME", self._connected_handler)
        self.watchMessage("SYS-CPING", self._ping_handler)

        self.send([
                  "SYS-INIT",
                  str(103),
                  appname,
                  appversion,
                  str(os.getpid()),
                  os.getcwd()
                  ])

        self.appname = appname
        self.running = True

        self.send(["SYS-ACCEPT", "*"])



    def _abort_handler(self, data):
        print " | ".join(data)
        sys.exit(1)

    def _connected_handler(self, data):
        print "connected",
        print " | ".join(data)
        return 0

    def _ping_handler(self, data):
        self.send(["SYS-CPONG"] + data[1:])

    def _process_message(self, msg):
        chunk = msg.rstrip('\n')
        data = chunk.split("\t")

        if data[0] in self.handler_table:
            ret = 0
            for handler in self.handler_table[data[0]]:
                ret = handler(data)
            return ret
        else:
            return self.default_handler(data)


    def receive(self):
        print "receive start"
        chunk = ""

        while(self.running):
            rdy_read, rdy_write, err = select.select([self.s], [], [], 1)

            if self.s in rdy_read:
                chunk += self.s.recv(8096)

                # The one message per packet thing is bunk.
                loc = chunk.find("\n")
                while loc != -1:
                    msg = chunk[:loc]
                    chunk = chunk[loc+1:]
                    loc = chunk.find("\n")

                    ret = self._process_message(msg)

                    if ret is not None and ret != 0:
                        print "leaving"
                        return ret

    def _conv(self, val):
        if val is None:
            return ""
        else:
            return str(val)

    def send(self, data):
        self.s.send("\t".join(map(self._conv,data)) + "\n")

    def sendDebug(self, data):
        self.send(["SYS-DEBUG", self.appname] + data)

    def sendLog(self, data):
        self.send(["SYS-LOG", self.appname] + data)

    def watchMessage(self, type, handler):
        if type not in self.handler_table:
            self.handler_table[type] = [handler]
        else:
            self.handler_table[type] += [handler]

    def defaultHandler(self, handler):
        self.default_handler = handler

    def exit(self):
        self.running = False

    def getVarList(self, appname):
        vl = ServIOVarList(self, appname)
        vl.refreshAll()
        return vl

class ServIOVarList:
    def __init__(self, servio, appname):
        self.appname = appname
        self.servio = servio
        self.vars = {}
        self.refresh_timeout = 30

        self.vars_available = {}
        self.available = threading.Event()

        # Handle these guys the same
        self.servio.watchMessage("SYS-SET", self.handleSysSet)
        self.servio.watchMessage("SYS-VALUE", self.handleSysSet)

        self.servio.watchMessage("SYS-UNSET", self.handleSysUnSet)

    def refreshAll(self):
        self.servio.send(["SYS-GET", self.appname])

    def handleSysSet(self, data):
        if data[1] != self.appname:
            return

        name = data[2]
        key = data[3]

        #print self.appname + ":" + str(data) + "..." + name + "?" + str(key)

        # refreshAll Get
        if data[0] == "SYS-VALUE" and name == "" and key == "":
            for n in data[4:]:
                if n not in self.vars_available:
                    self.vars_available[n] = threading.Event()

                self.vars_available[n].clear()
                self.servio.send(["SYS-GET", self.appname, n])

            self.available.set()
            return

        # A map
        if name[-1:] == "%":
            if key == "":
                self.vars[name] = {}
            else:
                if name not in self.vars:
                    self.vars[name] = {}

                self.vars[name][key] = data[4:]

        # Simple
        else:
            #print name + "<--" + str(data[4:])
            self.vars[name] = data[4:]

        if name not in self.vars_available:
            self.vars_available[name] = threading.Event()

        self.vars_available[name].set()


    def handleSysUnSet(self, data):
        if data[1] != self.appname:
            return

    def get(self, name, key, field):
        if not self.available.isSet():
            self.available.wait(self.refresh_timeout)
            if not self.available.isSet():
                print "refresh all timed out"
                return None

        if name not in self.vars_available:
            print name + " not in vars_available"
            return None

        print self.vars[name]

        if not self.vars_available[name].isSet():
            self.vars_available[name].wait(self.refresh_timeout)
            if not self.vars_available[name].isSet():
                print "Wait on variable failed for " + name
                # FIXME DEBUG


        if name[-1:] == "%":
            if key is None:
                print "No key on map fetch for " + name
                return None

            return self.vars[name][key][field]

        else:
            return self.vars[name][field]

    def set(self, name, key, value):
        if key is not None and name[-1:] != "%":
            name = name + "%"

        try:
            if key is not None:
                orig = self.vars[name][key]
            else:
                orig = self.vars[name]
        except:
            print "Couldn't find " + name + " in dict"
            print str(self.vars)
            orig = None

        if value == orig:
            return
        else:
            self.servio.send(["SYS-SET", self.appname, name, key, value])


