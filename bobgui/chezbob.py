from wxPython.wx import *
import sys
import threading
import time
import wx.lib.newevent

from bob_db import *
from user import *
from user_dialog import *
from login_panel import *
from password_panel import *


STATE_LOGIN = 1
STATE_PASSWORD = 2
STATE_PURCHASE = 3

class MainFrame(wxFrame):

    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title,
                wxDefaultPosition, wxSize(1024, 768))

        self.bob_db = BobDB()

        self.Bind(EVT_TEXT_ENTER, self.onTextEnter)

        self.state = STATE_LOGIN

        self.beginFuncTable = {}
        self.endFuncTable = {}

        self.makeLoginPanel()
        self.makePasswordPanel()



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
        self.loginPanel = LoginPanel(self, -1, wxPoint(0,0), self.GetSize())
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
        self.passwordPanel = PasswordPanel(self, -1, wxPoint(0,0), self.GetSize())
        self.passwordPanel.Layout()
        self.passwordPanel.Show(false)

        self.beginFuncTable[STATE_PASSWORD] = self.beginPassword
        self.endFuncTable[STATE_PASSWORD] = self.endPassword

        self.passwordErrorDialog = wxMessageDialog(self, 
                                                   "Password Mismatch",
                                                   "Password Mismatch",
                                                   wxOK | wxICON_EXCLAMATION)


    def beginPassword(self):
        print "beginPassword"
        self.passwordPanel.Clear()
        self.passwordPanel.Show()

    def endPassword(self):
        print "endPassword"
        self.passwordPanel.Clear()
        self.passwordPanel.Show(false)

    def onTextEnter(self, event):
        if self.state == STATE_LOGIN:
            login = self.loginPanel.GetLogin()
            # XXX VALIDATE LOGIN
            self.user = self.bob_db.getUserByUserName(login)

            if self.user is None:
                userDialog = UserDialog(self, 
                                        -1,
                                        "Enter your user information",
                                        login)
                userRet = userDialog.ShowModal()

                if userRet == wxID_OK:
                    # XXX Add the user
                    self.changeState(STATE_PURCHASE)
                else:
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
        self.loginDialog.EndModal(wxID_IGNORE)


class ChezApp(wxApp):
    def OnInit(self):
        self.frame = MainFrame(NULL, -1, "Welcome to ChezBob")
        self.SetTopWindow(self.frame)
        self.frame.Show(true)


        self.fun_thread = threading.Thread(target=self.fun_thread_func)
        self.fun_thread.start()

        #self.frame.beginLogin()
        self.frame.changeState(STATE_LOGIN)

        return true;

    def forceLogin(self, login):
        self.frame.forceLogin(login)

    def fun_thread_func(self):
        time.sleep(3)
        #self.forceLogin("test")

app = ChezApp(0)
app.MainLoop()
app.Exit()

