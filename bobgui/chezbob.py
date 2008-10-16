import wx
import sys
import threading
import time
import os
import wx.lib.newevent

from bob_db import *
from user import *
from user_dialog import *
from login_panel import *
from password_panel import *
from purchase_panel import *

import validate


STATE_LOGIN = 1
STATE_PASSWORD = 2
STATE_PURCHASE = 3

class MainFrame(wx.Frame):

    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, 
                         parent=parent, 
                         title=title,
                         size=wx.Size(1024, 768), 
                         style=0,
                         name="chezFrame")

        self.bob_db = BobDB()

        self.Bind(EVT_TEXT_ENTER, self.onTextEnter)

        self.state = STATE_LOGIN

        self.beginFuncTable = {}
        self.endFuncTable = {}

        self.makeLoginPanel()
        self.makePasswordPanel()
        self.makePurchasePanel()

    def changeState(self, new_state):
        print "change state %d" % new_state
        try:
            func = self.endFuncTable[self.state]
            func()
        except KeyError:
            print "couldn't find end for %s" % self.state
            pass

        self.state = new_state

        try:
            func = self.beginFuncTable[self.state]
            func()
        except KeyError:
            print "couldn't find begin for %s" % self.state
            pass

    def makeLoginPanel(self):
        self.loginPanel = LoginPanel(self, -1, wx.Point(0,0), self.GetSize())
        self.loginPanel.Layout()
        self.loginPanel.Show(false)

        self.beginFuncTable[STATE_LOGIN] = self.beginLogin
        self.endFuncTable[STATE_LOGIN] = self.endLogin


    def beginLogin(self):
        print "beginLogin"
        self.loginPanel.Clear()
        self.loginPanel.Show()

    def endLogin(self):
        print "endLogin"
        self.loginPanel.Clear()
        self.loginPanel.Show(false)

    def makePasswordPanel(self):
        self.passwordPanel = PasswordPanel(self, -1, wx.Point(0,0), self.GetSize())
        self.passwordPanel.Layout()
        self.passwordPanel.Show(false)

        self.beginFuncTable[STATE_PASSWORD] = self.beginPassword
        self.endFuncTable[STATE_PASSWORD] = self.endPassword

        self.passwordErrorDialog = wx.MessageDialog(self, 
                                                   "Password Mismatch",
                                                   "Password Mismatch",
                                                   wx.OK | wx.ICON_EXCLAMATION)


    def beginPassword(self):
        print "beginPassword"
        self.passwordPanel.Clear()
        self.passwordPanel.Show()

    def endPassword(self):
        print "endPassword"
        self.passwordPanel.Clear()
        self.passwordPanel.Show(false)

    def makePurchasePanel(self):
        self.purchasePanel = PurchasePanel(self, -1, wx.Point(0,0),
                self.GetSize())
        self.purchasePanel.Layout()
        self.passwordPanel.Show(false)

        self.beginFuncTable[STATE_PURCHASE] = self.beginPurchase
        self.endFuncTable[STATE_PURCHASE] = self.endPurchase

    def beginPurchase(self):
        self.purchasePanel.Clear()
        # XXX Fill in the nibbly bits
        self.purchasePanel.SetUserName(self.user.GetUserName())
        self.purchasePanel.SetBalance(self.user.GetBalance())
        self.purchasePanel.Show()

    def endPurchase(self):
        self.purchasePanel.Show(false)
        self.purchasePanel.Clear()


    def onTextEnter(self, event):
        if self.state == STATE_LOGIN:
            login = self.loginPanel.GetLogin()

            if not validate.validateUserName(login):
                validate.warnUserName(self, login)
                self.changeState(STATE_LOGIN)
                return

            self.user = self.bob_db.getUserByUserName(login)

            if self.user is None:
                newUserPrompt = wx.MessageDialog(self,
        "User %s not found, would you like to create a new account?" % login,
                                                "User not found.",
                                                wx.YES | wx.NO | wx.NO_DEFAULT)

                res = newUserPrompt.ShowModal()

                if res == wx.ID_YES:
                    userDialog = UserDialog(self, 
                                            -1,
                                            "Enter your user information",
                                            login)
                    userRet = userDialog.ShowModal()

                    if userRet == wx.ID_OK:
                        # XXX Add the user
                        # XXX Load the user
                        self.changeState(STATE_PURCHASE)
                    else:
                        self.changeState(STATE_LOGIN)
                else: # No new user
                    self.changeState(STATE_LOGIN)

            elif self.user.hasPassword():
                self.changeState(STATE_PASSWORD)
            else:
                self.changeState(STATE_PURCHASE)

        elif self.state == STATE_PASSWORD:
            password = self.passwordPanel.GetPassword()
            res = self.user.checkPassword(password)

            if not res:
                self.passwordErrorDialog.ShowModal()
                self.changeState(STATE_LOGIN)
            else:
                self.changeState(STATE_PURCHASE)

        else:
            event.Skip()

    def forceLogin(self, login):
        self.loginDialog.EndModal(wx.ID_IGNORE)


class ChezApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(NULL, -1, "Welcome to ChezBob")
        self.SetTopWindow(self.frame)
        self.frame.Show(true)

        self.fun_thread = threading.Thread(target=self.fun_thread_func)
        self.fun_thread.start()

        self.frame.changeState(STATE_LOGIN)

        return true;

    def forceLogin(self, login):
        self.frame.forceLogin(login)

    def fun_thread_func(self):
        time.sleep(3)
        #self.forceLogin("test")

    def OnRun():
        return wx.App.OnRun()


# Set the theme
os.environ['GTK2_RC_FILES'] = 'ChezTheme/gtk-2.0/gtkrc'

app = ChezApp(0)
app.MainLoop()
app.Exit()

