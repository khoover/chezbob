#!/usr/bin/python

import servio
import threading
import time
import sys
import random
import FPCtrl

from servio import genTag

class SodaUser:

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
        self.time = 0
        self.timeout = timeout
        self.balance = int(balance)
        self.servio = servio

        self.servio.sendLog("User " + login + " Logged In")

        self.ui = ui
        self.resetTTL()

        self.vend_in_progress = False
        self.barcode_vend_in_progress = False
        self.escrow_in_progress = False

        self.item = None

        self.should_logout = False # Whether to logout on transaction
                                   # completion

        self.ui.logIn(self)

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
        self.ui.updateTTL(self)

    def isAnon(self):
        return self.anon

    def getBalance(self):
        return self.balance

    def setBalance(self, amount):
        self.balance = amount
        self.ui.updateBalance(self)

    def getLogin(self):
        return self.login

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
            self.resetTTL()

            if self.anon and self.balance < item['price']:
                print "Purchase request for " + item['name'] + " denied"
                print "Insufficient Funds"

                self.ui.vendDeny(self, "INSUFFICIENT FUNDS")
                self.barcode_vend_in_progress = False

                return False

            return self.endBarCodeSuccess(item)

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


    def makePurchase(self, item):
        '''
        You need to have guards in place that item exists
        '''

        self.querytag = genTag()

        price = item['price']
        if self.anon:
            # For anonymous purchases, round the item price up to the next
            # multiple of five cents, since we are unable to return change
            # except in five cent increments.
            price += 4
            price = (price // 5) * 5

            self.servio.send(["BOBDB-DEPOSIT",
                              genTag(),
                              self.login,
                              price])
            self.servio.send(["BOBDB-PURCHASE",
                              self.querytag,
                              self.login,
                              item['barcode'],
                              price])
        else:
            self.servio.send(["BOBDB-PURCHASE",
                             self.querytag,
                             self.login,
                             item['barcode']])
            self.servio.send(["SOUND-PLAY","purchased"])

        print "Charged " + self.login + ": " + str(price) + "c"
        self.setBalance(self.balance - price)
        self.ui.vendComplete(self, item['name'], price)

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

        self.makePurchase(self.item)

        self.vend_in_progress = False
        self.item = None

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
        self.barcode_vend_in_progress = True

        self.barcodequerytag = "B" + genTag()

        self.servio.send(["BOBDB-QUERYPRODUCT",
                          self.barcodequerytag,
                          itemid]);

        print "Barcode scan " + itemid + " sent to DB"

    def endBarCodeSuccess(self, item = None):
        '''
        Return True if the user should be logged out.
        '''
        self.makePurchase(item)

        self.barcode_vend_in_progress = False

        return (self.anon or self.shouldLogout()) and self.canLogout()
