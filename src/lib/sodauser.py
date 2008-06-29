#!/usr/bin/python

import servio
import threading
import time
import sys
import random
import FPCtrl

from servio import genTag

class SodaUserBase:
    def __init__(self,
                 anon,
                 login,
                 timeout,
                 balance):
        self.anon = anon
        self.login = login
        self.timeout = timeout
        self.balance = balance

    def isAnon(self):
        return self.anon

    def getBalance(self):
        return self.balance

    def setBalance(self, amount):
        self.balance = amount

    def getLogin(self):
        return self.login




class SodaUser(SodaUserBase):
    fp_learn_count = 3

    def __init__(self, 
                 anon=False, 
                 login="anonymous", 
                 timeout=30, 
                 balance=0,
                 servio=None,
                 ui=None,
                 fpctrl=None):

        print "User " + login + " Logged In"

        base.__init__(anon, login, timeout, balance)

        self.servio = servio

        self.servio.sendLog("User " + login + " Logged In")

        self.resetTTL()

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

        self.FPCtrl = fpctrl

        # Turn off the finger print reader during login
        self.FPCtrl.doDisable()

        if not self.anon:
            self.alquerytag = "A" + genTag()
            self.servio.send(["BOBDB-QUERYUSERPREF",
                              self.alquerytag,
                              self.login,
                              "Auto Logout"])

    def __del__(self):
        print "Logging " + self.login + " out"
        self.servio.sendLog("User " + self.login + " Logged Out")

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

        self.FPCtrl.doLoginMode()

        self.ui.logOut(self)

    def canLogout(self):
        return not (self.vend_in_progress\
                    or self.barcode_vend_in_progress\
                    or self.escrow_in_progress)

    def doLogout(self):
        if not self.canLogout():
            self.should_logout = True
            print "Not Logging Out vip: " + str(self.vend_in_progress) + \
                  " bvip: " + str(self.barcode_vend_in_progress) + \
                  " eip: " + str(self.escrow_in_progress)
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
        self.ui.showTick(self)
        return self.getTTL() <= 0

    def resetTTL(self):
        # Kick UI
        self.time = int(time.time())

    def isLearningFp(self):
        return self.fp_learn_in_progress

    def setBalance(self, amount):
        base.setBalance(amount)
        self.ui.updateBalance(self)

    def getTTL(self):
        return self.time + self.timeout - int(time.time())

    def setUserPref(self, pref, value):
        #print "User Pref " + pref + " " + value
        if pref == "Auto Logout" and int(value) == 1:
            #print "Setting Autologout"
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
                self.resetTTL()

            return False

        elif self.barcode_vend_in_progress and item['tag'] == self.barcodequerytag:
            self.item = item

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

        #print "Pre-Balance: " + str(self.getBalance())
        # Strictly to update the GUI
        self.setBalance(self.balance - self.item['price'])
        #print "Post-Balance: " + str(self.getBalance())

        self.ui.vendComplete(self, self.item['name'], self.item['price'])

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

        self.FPCtrl.doLearnMode()

        self.fp_learn_in_progress = True
        self.fp_list = []

        self.resetTTL()


    def endFpLearn(self, FPServVL):
        if self.anon:
            return

        self.fp_learn_in_progress = False
        self.FPCtrl.doDisable()

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
            self.ui.fpLearnFail(self, 
                                self.fp_learn_count, 
                                exinfo + " " + message)
        else:
            self.FPCtrl.doDisable()

            self.servio.send(["FP-UNPERSIST", self.login])
            # XXX Silly name for a finger
            self.servio.send(["FP-PERSIST", fpidr, self.login, "bob"])

            print "Persisiting " + self.login + " with " + str(fpidr)

            self.ui.fpLearnSuccess(self, "")
            self.fp_learn_in_progress = False

        self.fp_list = []
        self.resetTTL()
