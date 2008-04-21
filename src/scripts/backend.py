#!/usr/bin/python

import servio
import threading
import time
import sys
import random
import mozui

# Verified FP Learn
# Verified FP Login
# Verified Barcode Vend
# Verified Anonymous Barcode Vend
# Verified Soda Vend


# Escrow is broken in MDB

def genTag():
    return str(random.randint(0,1<<32))

class SodaUser:
    fp_learn_count = 3

    def __init__(self, 
                 anon=False, 
                 login="anonymous", 
                 timeout=30, 
                 balance=0,
                 servio=None,
                 ui=None):

        print "User " + login + " Logged In"
        self.anon = anon        # User is anonymous.  Escrow mode.
        self.login = login
        self.timeout = timeout
        self.ttl = timeout
        self.balance = int(balance)
        self.servio = servio

        self.vend_in_progress = False
        self.barcode_vend_in_progress = False
        self.escrow_in_progress = False

        # Less critical
        self.fp_learn_in_progress = False

        self.itemid = 0
        self.item = None

        self.should_logout = False # Whether to logout on transaction
                                   # completion

        self.ui = ui
        self.ui.logIn(self)

        if not self.anon:
            self.alquerytag = "A" + genTag()
            self.servio.send(["BOBDB-QUERYUSERPREF",
                              self.alquerytag,
                              self.login,
                              "Auto Logout"])

    def __del__(self):
        print "Logging " + self.login + " out"

        if self.anon and self.balance > 0:
            print "Returning change for anonymous user"
            self.servio.sendLog(["RETURNING " \
                                 + str(self.balance)\
                                 + " TO ANONYMOUS USER ON LOGOUT"])
            # This is nominally what should be used, but it is somewhat
            # broken
            self.servio.send(["CASH-REJECT"])

            self.servio.send(["CASH-CHANGE", self.balance])


        if self.fp_learn_in_progress:
            # TODO Tidy
            pass

        self.ui.logOut(self)

    def canLogout(self):
        return not (self.vend_in_progress\
                    or self.barcode_vend_in_progress\
                    or self.escrow_in_progress)

    def doLogout(self):
        if not self.canLogout():
            self.should_logout = True
            print "Not Logging Out"
            print "vip: " + str(self.vend_in_progress)
            print "bvip: " + str(self.barcode_vend_in_progress)
            print "eip: " + str(self.escrow_in_progress)
            return False

        else:
            return True

    # Does not imply canLogout
    def shouldLogout(self):
        if self.should_logout:
            return True
        else:
            # TODO ensure auto-logout has been checked or resolve race
            return False

    def tickDown(self):
        '''
        Return true if the time has expired
        '''
        self.ttl = self.ttl - 1
        self.ui.showTick(self)
        self.ui.updateBalance(self)
        return self.ttl <= 0

    def resetTTL(self):
        # Kick UI
        self.ttl = self.timeout

    def isAnon(self):
        return self.anon

    def isLearningFp(self):
        return self.fp_learn_in_progress

    def getBalance(self):
        return self.balance

    def setBalance(self, amount):
        self.balance = amount
        self.ui.updateBalance(self)

    def getLogin(self):
        return self.login

    def getTTL(self):
        return self.ttl

    def setUserPref(self, pref, value):
        print "User Pref " + pref + " " + value
        if pref == "Auto Logout" and int(value) == 1:
            print "Setting Autologout"
            self.should_logout = True

    def beginEscrow(self):
        self.escrow_in_progress = True
        self.resetTTL()

    def deposit(self, amount):
        self.escrow_in_progress = False

        self.balance += amount

        if not self.anon:
            print "Updating DB with Deposit"
            self.querytag = genTag()
            self.servio.send(["BOBDB-DEPOSIT",
                              self.querytag,
                              self.login,
                              amount])

            self.servio.sendLog(["deposited money into " + self.login \
                                 + ": " + str(self.balance)])

        self.resetTTL()
        self.ui.updateBalance(self)


    def beginVend(self, itemid):
        self.cur_itemid = itemid
        self.querytag = genTag()
        self.vend_in_progress = True

        self.servio.send(["BOBDB-QUERYPRODUCT",
                          self.querytag,
                          self.cur_itemid])

    def readProductInfo(self, item):
        '''
        Returns True if the user should logout
        '''
        if self.vend_in_progress and item['tag'] == self.querytag:
            self.item = item

            # Deny Anonymous if there are insufficient funds
            if self.anon and self.balance < self.item['price']:
                print "Purchase request for " + self.item['name'] + " denied"
                print "Insufficient Funds"

                self.servio.send(["VEND-DENIED"])

                self.resetTTL()
                self.ui.vendDeny(self, "INSUFFICIENT FUNDS")
                self.vend_in_progress = False
                self.item = None
            else:
                print "Purchase request for " + self.item['name'] + " approved"
                self.servio.send(["VEND-APPROVED"])
                self.ui.vendComplete(self, self.item['name'])
                self.resetTTL()

            return False

        elif self.barcode_vend_in_progress and item['tag'] == self.barcodequerytag:
            self.item = item

            self.ui.vendComplete(self, self.item['name'])
            self.resetTTL()

            return self.endBarCodeSuccess()

        else:
            print "Got Unexpected Product Info " + str(item)
            self.resetTTL()
            return False

    def lookupFail(self, tag):
        if self.vend_in_progress and tag == self.querytag:
            self.vend_in_progress = False
        elif self.barcode_vend_in_progress and tag == self.barcodequerytag:
            self.barcode_vend_in_progress = False
        # TODO Kick UI


    def makePurchase(self):
        '''
        You need to have guards in place that item exists
        '''
        self.querytag = genTag()
        self.servio.send(["BOBDB-PURCHASE",
                         self.querytag,
                         self.login,
                         self.item['barcode']])
        print "Charged " + self.login + ": " + str(self.item['price']) + "c"

        # Strictly to update the GUI
        self.setBalance(self.balance - self.item['price'])

        if self.anon:
            self.servio.send(["BOBDB-DEPOSIT",
                              self.querytag,
                              self.login,
                              self.item['price']])


    def endVendSuccess(self):
        '''
        Returns True if the user should be logged out.
        '''
        print "Vend-Success"
        if not self.vend_in_progress:
            self.servio.sendDebug(["DOUBLE CHARGE AVOIDED"])
            return self.anon or self.shouldLogout()

        if self.item is None:
            print "VEND SUCCESS WITH NO ITEM!!!!!!!!"
            self.servio.sendDebug(["Got VEND-SUCCESS w/o item data!!!"])
            return True

        self.makePurchase()

        self.vend_in_progress = False
        self.item = None
        self.itemid = None

        return (self.anon or self.shouldLogout()) and self.canLogout()

    def endVendFail(self):
        '''
        Returns True if the user should be logged out.
        '''

        print "No Soda Vended"

        self.ui.vendFail(self)

        self.vend_in_progress = False
        self.item = None

        return self.anon and self.canLogout()

    def beginBarCode(self, itemid):
        self.itemid = itemid
        self.barcode_vend_in_progress = True

        self.barcodequerytag = "B" + genTag()

        self.servio.send(["BOBDB-QUERYPRODUCT",
                          self.barcodequerytag,
                          self.itemid]);

        print "Barcode scan " + self.itemid + " sent to DB"

    def endBarCodeSuccess(self):
        '''
        Return True if the user should be logged out.
        '''
        self.makePurchase()

        self.barcode_vend_in_progress = False
        self.item = None
        self.itemid = 0

        return (self.anon or self.shouldLogout()) and self.canLogout()

    def beginFpLearn(self, FPServVL):
        if self.anon:
            return

        FPServVL.set("capture_match", None, "0")
        self.fp_learn_in_progress = True
        self.fp_list = []

        self.resetTTL()

    def endFpLearn(self, FPServVL):
        if self.anon:
            return

        self.fp_learn_in_progress = False
        FPServVL.set("capture_match", None, "1")
        FPServVL.set("visible", None, "0")

    def gotBadFpRead(self, id):
        if self.fp_learn_in_progress:
            self.fp_list = self.fp_list + [id]
            if len(self.fp_list) >= self.fp_learn_count:
                self.servio.send(["FP-LEARN"] + self.fp_list)
            else:
                print "Have " + str(len(self.fp_list)) + " fingerprints"

            self.ui.fpRead(self, self.fp_learn_count - len(self.fp_list))

            self.resetTTL()
        else:
            print "Didn't expect bad FP Read"

    def gotGoodFpRead(self, id, name):
        if not self.anon and self.fp_learn_in_progress:
            print "GOOD FP while learning someone else.  Unlearning"
            self.servio.send(["FP-UNPERSIST", id])

    def gotLearnDone(self, FPServVL, fpidr, result, exinfo, message):
        if self.anon or not self.fp_learn_in_progress:
            return

        if int(fpidr) == 0:
            print "Error Learning"
            self.ui.fpLearnFail(self, exinfo + " " + message)
            self.ui.fpCount(self, self.fp_learn_count)
        else:
            FPServVL.set("capture_match", None, "1")
            self.servio.send(["FP-UNPERSIST", self.login])
            # XXX Silly name for a finger
            self.servio.send(["FP-PERSIST", fpidr, self.login, "bob"])

            print "Persisiting " + self.login + " with " + str(fpidr)

            self.ui.fpLearnSuccess(self, "")
            self.fp_learn_in_progress = False

        self.fp_list = []
        self.resetTTL()


class SodaBackend:
    ttl_tick = 1
    current_user = None
    #appname = "PySodaBackend"
    appname = "BACKEND" # Needs to be this to get the soda# vars

    # Make sure the Vending Machine is Online
    vmcTimeout = 60*60
    vmcTTL = vmcTimeout

    def __init__(self):
        self.bus = servio.ServIO(self.appname, "0.0")

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

        self.escrow_reject_threshold = 500

        self.ui = mozui.MozUI(self.bus)

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

        if len(data) == 3:
                self.current_user = SodaUser(login=data[1],
                                             balance=data[2],
                                             servio=self.bus,
                                             ui=self.ui)
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
        if self.current_user.endVendSuccess():
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
                                         ui=self.ui)
            self.bus.send(["LOGIN-SUCCEEDED"])
            print "Login OK"
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

            self.current_user = SodaUser(anon=True, servio=self.bus, ui=self.ui)

        self.current_user.beginEscrow()

        # XXX Not until escrow is fixed and we actually use it
        #if not self.current_user.isAnon():
        self.bus.send(["CASH-ACCEPT"])

    def handleDeposit(self, data):
        amount = int(data[1])

        # Anonymous Login
        if self.current_user is None:
            self.current_user = SodaUser(anon=True, servio=self.bus, ui=self.ui)

        self.current_user.deposit(amount)

    def handleReturn(self, data):
        if self.current_user is not None:
            if self.current_user.doLogout():
                # Destructor takes care of coin return and UI update
                self.current_user = None
        else:
            print "Random Coin Return Press"

    def handleUnimplemented(self, data):
        print "Unimplemented " + str(data)

    def MainLoop(self):
        running = True

        self.bus.send(["VEND-SSTART", "0"])
        self.MdbVL.set("enabled", None, "7")

        #self.handleVendRequest(["VEND-REQUEST", "1"])

        # Show the login screen when we start.
        self.ui.logOut(None)

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
            except KeyboardInterrupt:
                print "kb interrupt"
                self.Exit()
                sys.exit(1)
            except:
                # Try to resume?
                self.Exit()
                sys.exit(1)

    def Exit(self):
        self.bus.exit()


backend = SodaBackend()
backend.MainLoop()
