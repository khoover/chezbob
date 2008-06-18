#!/usr/bin/python

import servio
import threading
import time
import sys
import random
import pyui
import unionui
import FPCtrl

from servio import genTag
from sodauser import SodaUser

# Verified FP Learn
# Verified FP Login
# Verified Barcode Vend
# Verified Anonymous Barcode Vend
# Verified Soda Vend


# Escrow is broken in MDB

class SodaBackend:
    ttl_tick = 1
    current_user = None
    #appname = "PySodaBackend"
    appname = "BACKEND" # Needs to be this to get the soda# vars

    # Make sure the Vending Machine is Online
    vmcTimeout = 60*60
    vmcTTL = vmcTimeout

    def __init__(self):
        self.bus = servio.ServIO(self.appname, "1.0", "0:u")

        self.bus.defaultHandler(servio.noop_handler)

        self.bus.watchMessage("LOGIN",             self.handleLogin)
        self.bus.watchMessage("LOGOUT",            self.handleLogout)

        self.bus.watchMessage("VEND-READY",        self.handleVendReady)
        self.bus.watchMessage("VEND-REQUEST",      self.handleVendRequest)
        self.bus.watchMessage("VEND-SUCCESS",      self.handleVendSuccess)
        self.bus.watchMessage("VEND-FAILED",       self.handleVendFailed)
        self.bus.watchMessage("VEND-SDONE",        self.handleVendSdone)
        self.bus.watchMessage("VEND-READY",        self.handleVendSdone)

        self.bus.watchMessage("BOBDB-USERPREF",    self.handleBobDBUserPref)
        self.bus.watchMessage("BOBDB-USERINFO",    self.handleBobDBUserInfo)
        self.bus.watchMessage("BOBDB-PRODUCTINFO", self.handleBobDBProductInfo)
        self.bus.watchMessage("BOBDB-FAIL",        self.handleBobDBFail)

        self.bus.watchMessage("FP-BADREAD",        self.handleFpBadRead)
        self.bus.watchMessage("FP-GOODREAD",       self.handleFpGoodRead)
        self.bus.watchMessage("FP-LEARN-DONE",     self.handleFpLearnDone)

        self.bus.watchMessage("LEARNSTART",        self.handleLearnStart)
        self.bus.watchMessage("LEARNEND",          self.handleLearnEnd)

        self.bus.watchMessage("CASH-ESCROW",       self.handleEscrow)
        self.bus.watchMessage("CASH-DEPOSIT",      self.handleDeposit)
        self.bus.watchMessage("CASH-RETURN",       self.handleReturn)

        self.bus.watchMessage("BARCODE-SCAN",       self.handleBarCodeScan)

        self.bus.watchMessage("SV-LEARN",          self.handleUnimplemented)

        self.bus.watchMessage("UI-READY",          self.handleUnimplemented)

        self.bus.watchMessage("BACK",              self.handleUnimplemented)

        self.bus_thread = threading.Thread(target=self.bus.receive)
        self.bus_thread.start()

        self.StartUpVL = self.bus.getVarList(self.appname)
        self.FPServVL  = self.bus.getVarList("FPSERV")
        self.MdbVL     = self.bus.getVarList("MDBSERV")

        self.FPCtrl = FPCtrl.FPCtrl(self.bus)

        self.escrow_reject_threshold = 500

        # Switch back to get both old mozilla and new pyui
        # simultaneously
        #self.ui = unionui.UnionUI(self.bus)
        # PyUI is missing something in the interface and inducing
        # crashes.
        self.ui = pyui.PyUI(self.bus)

    def handleLogin(self, data):
        # Having User and Balance Defined indicates sucessful pwless
        # login

        # XXX Dirty moz-kiosk workaround
        if (data[1] == "" or data[1] is None) and len(data) == 3:
            print "MOZ HACK Overriding login with " + str(self.last_login)
            data[1] = self.last_login

        if data[1] == "" or data[1] is None:
            print "Login Empty, Ignoring"
            return

        if self.current_user is not None:
            print "Someone already logged in"
            # Fixed to avoid race issue.
            self.bus.send(["LOGIN-FAILED"])
            return

        if len(data) == 3:
                self.current_user = SodaUser(login=data[1],
                                             balance=data[2],
                                             servio=self.bus,
                                             ui=self.ui,
                                             fpctrl=self.FPCtrl)
                self.bus.send(["LOGIN-SUCCEEDED"])
        else:
            print "DB Request for " + data[1]
            self.querytag = genTag()
            self.bus.send(["BOBDB-QUERYUSER",
                           self.querytag,
                           data[1]])

    def handleLogout(self, data):
        if self.current_user is not None and self.current_user.doLogout():
            self.current_user = None


    def handleVendRequest(self, data):
        self.canType = int(data[1])

        if self.current_user is None:
            print "No Escrow/User, denying Vend"
            self.bus.send(["VEND-DENIED"])
            return

        print "Handling VEND-REQUEST for can " \
                + str(self.canType) \
                + " and sending DB request for price"
        itemid = self.StartUpVL.get("soda" + str(self.canType), None, 0)

        print "Item id: " + str(itemid)

        self.current_user.beginVend(itemid)


    def handleVendSuccess(self, data):
        # Log the user out if necessary
        if self.current_user is not None and self.current_user.endVendSuccess():
            # Logout happens in the destructor
            self.current_user = None


    def handleVendFailed(self, data):
        print "No Soda Vended"

        if self.current_user.endVendFail():
            self.current_user = None


    def handleVendSdone(self, data):
        balance = 0
        self.vmcTTL = self.vmcTimeout

        if self.current_user is not None:
            if self.current_user.getBalance() > 0:
                balance = self.current_user.getBalance()

        self.bus.send(["VEND-SSTART", str(balance)])

    def handleVendReady(self, data):
        self.vmcTTL = self.vmcTimeout

    def handleBobDBUserPref(self, data):
        if self.current_user is not None:
            self.current_user.setUserPref(data[2], data[3])

    def handleBobDBUserInfo(self, data):
        tag = data[1]
        login = data[2]
        balance = data[3]
        if len(data) == 5 and data[4] != "":
            pw = data[4]
        else:
            pw = None

        if login == "" or login is None:
            print "Empty User String"
            return

        if tag != self.querytag:
            print "Unexpected user query" + str(data)
            return

        # Skip Password
        # B = Barcode login
        # F = Finger Print
        if tag[0] == 'F' or tag[0] == 'B' or pw is None:
            self.current_user = SodaUser(servio=self.bus,
                                         login=login,
                                         balance=balance,
                                         ui=self.ui,
                                         fpctrl=self.FPCtrl)
            self.bus.send(["LOGIN-SUCCEEDED"])
            #print "Login OK"
        else:
            print "Setting last_login to " + str(data[2])
            self.last_login = data[2]
            self.ui.passwordLogin(login=data[2],
                                    balance=data[3],
                                    hash=data[4])
            print str(data)


    def handleBobDBProductInfo(self, data):
        querytag = data[1]

        if self.current_user is None:
            print "Unexpected Product Info"
            return

        item = {
                'tag' : data[1],
                'barcode' : str(data[2]),
                'name' : data[3],
                'price' : int(data[4]),
                'stock' : data[5]
               }

        # This can signal a purchase via barcode
        if self.current_user.readProductInfo(item):
            self.current_user = None


    def handleBobDBFail(self, data):
        if self.current_user is None:
            if data[2] == "NO-USER":
                pass
        else:
            if data[2] == "NO-USER":
                print "Didn't expect user query mid transaction"
            elif data[2] == "NO-PRODUCT":
                self.current_user.lookupFail(data[1])

    def handleFpBadRead(self, data):
        if self.current_user is None:
            print "BAD FP READ"
        else:
            self.current_user.gotBadFpRead(data[1])

    def handleFpGoodRead(self, data):
        if self.current_user is None:
            print "GOOD FP: Sending DB Request for " + data[2]
            self.querytag = "F" + genTag();
            self.bus.send(["BOBDB-QUERYUSER",
                            self.querytag,
                            data[2]])
        else:
            self.current_user.gotGoodFpRead(id=data[1], name=data[2])

    def handleFpLearnDone(self, data):
        if self.current_user is None:
            print "Didn't expect Learn Done without a user"
        else:
            fpidr = data[1]
            result = data[2]
            exinfo = data[3]
            message = data[4]

            self.current_user.gotLearnDone(self.FPServVL, 
                                           fpidr,
                                           result,
                                           exinfo,
                                           message)

        print "fp learn done"

    def handleLearnStart(self, data):
        if self.current_user is not None:
            self.current_user.beginFpLearn(self.FPServVL)
        else:
            print "Unexpected LearnStart"

    def handleLearnEnd(self, data):
        if self.current_user is not None:
            self.current_user.endFpLearn(self.FPServVL)
        else:
            print "Unexpected LearnEnd"

    def handleBarCodeScan(self, data):
        if self.current_user is None:
            self.querytag = "B" + genTag()
            self.bus.send(["BOBDB-QUERYUSER",
                           self.querytag,
                           data[1]])
            print "Sending to QueryUser " + data[1]
        else:
            self.current_user.beginBarCode(data[1])

    def handleEscrow(self, data):
        amount = int(data[1])
        # Anonymous Login
        if self.current_user is None:

            if amount >= self.escrow_reject_threshold:
                self.bus.send(["CASH_REJECT"])
                return

            if amount == 0:
                print "Not logging in without balance..."
                return

            self.current_user = SodaUser(anon=True, 
                                         servio=self.bus, 
                                         ui=self.ui,
                                         fpctrl=self.FPCtrl)

        self.current_user.beginEscrow()

        # XXX Not until escrow is fixed and we actually use it
        #if not self.current_user.isAnon():
        self.bus.send(["CASH-ACCEPT"])

    def handleDeposit(self, data):
        amount = int(data[1])

        # XXX This may be redundant with handleEscrow above
        # Anonymous Login
        if self.current_user is None:
            self.current_user = SodaUser(anon=True, 
                                         servio=self.bus, 
                                         ui=self.ui,
                                         fpctrl=self.FPCtrl)

        self.current_user.deposit(amount)

    def handleReturn(self, data):
        if self.current_user is not None:
            if self.current_user.doLogout():
                # Destructor takes care of coin return and UI update
                self.current_user = None
        else:
            print "Random Coin Return Press"

    def handleUnimplemented(self, data):
        #print "Unimplemented " + str(data)
        pass

    def MainLoop(self):
        running = True

        self.bus.send(["VEND-SSTART", "0"])
        self.MdbVL.set("enabled", None, "7")

        #self.handleVendRequest(["VEND-REQUEST", "1"])

        # Show the login screen when we start.
        self.ui.logOut(None)
        self.FPCtrl.doLoginMode()

        while running:
            try:
                time.sleep(self.ttl_tick)

                self.vmcTTL = self.vmcTTL - 1

                if self.current_user is not None:
                    # See if the timeout has expired
                    if self.current_user.tickDown():
                        print "Timed out"
                        self.current_user = None
                else:
                    # Make sure we didn't wedge in learning
                    self.FPServVL.set("capture_match", None, "1")
                    self.MdbVL.set("enabled", None, "7")

                if not self.bus_thread.isAlive():
                    print "Bus Disappeared... Exiting"
                    self.Exit()
                    sys.exit(1)

            except KeyboardInterrupt:
                print "kb interrupt"
                self.Exit()
                sys.exit(1)
            except:
                # Try to resume?
                print "Exception, exiting"
                self.Exit()
                sys.exit(1)
                raise

    def Exit(self):
        self.bus.exit()


backend = SodaBackend()
backend.MainLoop()
