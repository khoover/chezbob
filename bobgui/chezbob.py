from wxPython.wx import *
import sys
import threading
import time
import wx.lib.newevent

from bob_db import *
from user import *
from user_dialog import *


class MainFrame(wxFrame):
    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title,
                wxDefaultPosition, wxSize(1024, 768))

        self.bob_db = BobDB()

    def beginLogin(self):
        while not self.doLogin():
            pass


    def doLogin(self):
        self.loginDialog = wxTextEntryDialog(self, 
                                        "Please enter your username",
                                        "Please enter your username",
                                        "", # Default Value
                                        wxOK | wxCENTRE)

        passwordDialog = wxPasswordEntryDialog(self,
                                               "Please enter your password",
                                               "Please enter your password",
                                               "",
                                               wxOK | wxCANCEL | wxCENTRE)

        passwordErrorDialog = wxMessageDialog(self, 
                                           "Password Mismatch",
                                           "Password Mismatch",
                                           wxOK | wxICON_EXCLAMATION)

        ret = wxCANCEL

        # wxID_IGNORE == barcode
        while ret != wxID_OK and ret != wxID_IGNORE:
            ret = self.loginDialog.ShowModal()

        print self.loginDialog.GetValue()

        # XXX Validate login
        if self.loginDialog.GetValue() == "":
            return False

        if ret == wxID_OK: # XXX Check for PW in DB
            self.user = self.bob_db.getUserByUserName(self.loginDialog.GetValue())
            if self.user is None:
                userDialog = UserDialog(self, 
                                        -1,
                                        "Enter your user information",
                                        self.loginDialog.GetValue())
                userRet = userDialog.ShowModal()

                if userRet == wxID_OK:
                    # XXX Add the user
                    return true;
                else:
                    return false

            elif self.user.hasPassword():
                passwordDialog.ShowModal()

                res = self.user.checkPassword(passwordDialog.GetValue())

                if not res:
                    passwordErrorDialog.ShowModal()
                    return False

        return True

    def forceLogin(self, login):
        self.loginDialog.EndModal(wxID_IGNORE)


class ChezApp(wxApp):
    def OnInit(self):
        self.frame = MainFrame(NULL, -1, "Welcome to ChezBob")
        self.SetTopWindow(self.frame)
        self.frame.Show(true)

        self.fun_thread = threading.Thread(target=self.fun_thread_func)
        self.fun_thread.start()

        self.frame.beginLogin()

        return true;

    def forceLogin(self, login):
        self.frame.forceLogin(login)

    def fun_thread_func(self):
        time.sleep(3)
        #self.forceLogin("test")

app = ChezApp(0)
app.MainLoop()
app.Exit()

