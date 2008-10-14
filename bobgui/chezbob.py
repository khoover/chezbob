from wxPython.wx import *
import sys
import threading
import time
import wx.lib.newevent

class UserDialog(wxDialog):
    def __init__(self, parent, ID, title, username):
        wxDialog.__init__(self, parent, ID, title)

        windowSize = self.GetVirtualSize()

        topSizer = wxBoxSizer(wxVERTICAL)
        boxSizer = wxBoxSizer(wxVERTICAL)

        topSizer.Add(boxSizer, 0, wxALIGN_CENTER_HORIZONTAL|wxALL, 5)

        noticeTxt = "We did not find the login information for %s." % username
        notice = wxStaticText(self, -1, noticeTxt, style=wxALIGN_LEFT)
        boxSizer.Add(notice, wxALIGN_CENTER)

        enterTxt = "If you do not already have an account, fill in the form below to create one"
        enter = wxStaticText(self, -1, enterTxt, style=wxALIGN_LEFT)

        enter.Wrap(windowSize.GetWidth())
        boxSizer.Add(enter, wxALIGN_CENTER)

        dataSizer = wxFlexGridSizer(2, 2, 5, 10)

        userNameLabel = wxStaticText(self, -1, "Username: ")
        dataSizer.Add(userNameLabel)

        self.userNameInput = wxTextCtrl(self,
                                        -1,
                                        username,
                                        wxDefaultPosition,
                                        wxSize(300, -1))

        dataSizer.Add(self.userNameInput)


        emailLabel = wxStaticText(self, -1, "Email: ")
        dataSizer.Add(emailLabel)

        self.emailInput = wxTextCtrl(self, 
                                     -1, 
                                     "",
                                     wxDefaultPosition,
                                     wxSize(300, -1))
        dataSizer.Add(self.emailInput)

        boxSizer.AddSpacer(wxSize(10,10))
        boxSizer.Add(dataSizer, wxALIGN_LEFT)


        boxSizer.AddSpacer(wxSize(10,10))

        boxSizer.Add(wxStaticLine(self, 
                                  -1, 
                                  size = wxSize(windowSize.GetWidth(),-1)), 
                                  wxALL, 
                                  5)

        boxSizer.AddSpacer(wxSize(10,10))

        buttons = self.CreateButtonSizer(wxOK | wxCANCEL)
        buttons.Realize()

        boxSizer.Add(buttons)

        self.SetSizer(topSizer)
        self.Fit()

        self.emailInput.SetFocus()
    pass

    def Validate(self):
        # XXX
        return true;

class User:
    check_password = true

    def loadFromUsername(self, username):
        pass

    def loadFromBarcode(self, barcode):
        pass

    def hasPassword(self):
        return check_userpassword and true # FIXME


class MainFrame(wxFrame):
    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title,
                wxDefaultPosition, wxSize(1024, 768))

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

        ret = wxCANCEL

        # wxID_IGNORE == barcode
        while ret != wxID_OK and ret != wxID_IGNORE:
            ret = self.loginDialog.ShowModal()

        print self.loginDialog.GetValue()

        # XXX Validate login
        if self.loginDialog.GetValue() == "":
            return false

        if ret == wxID_OK: # XXX Check for PW in DB
            self.user = User()

            if not self.user.loadFromUsername(self.loginDialog.GetValue()):
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
                print passwordDialog.GetValue()

        return true

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

