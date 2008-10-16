from wxPython.wx import *
import re
import validate

class UserDialog(wxDialog):
    """
    A Dialog to enter email information for the initial account
    creation.
    """


    def __init__(self, parent, ID, title, username):
        wxDialog.__init__(self, 
                          parent=parent, 
                          title=title)

        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetForegroundColour(parent.GetForegroundColour())

        font = self.GetFont();
        font.SetPointSize(20)
        self.SetFont(font)

        windowSize = self.GetVirtualSize()

        topSizer = wxBoxSizer(wxVERTICAL)
        boxSizer = wxBoxSizer(wxVERTICAL)

        topSizer.Add(boxSizer, 0, wxALIGN_CENTER_HORIZONTAL|wxALL, 5)

        noticeTxt = "We did not find the login information for %s." % username
        notice = wxStaticText(self, -1, noticeTxt, style=wxALIGN_LEFT)

        enterTxt = "If you do not already have an account, fill in the form below to create one"
        enter = wxStaticText(self, -1, enterTxt, style=wxALIGN_LEFT)

        enter.Wrap(windowSize.GetWidth())

        userNameLabel = wxStaticText(self, -1, "Username: ")

        self.userNameInput = wxTextCtrl(self,
                                        -1,
                                        username,
                                        wxDefaultPosition,
                                        wxSize(300, -1))

        emailLabel = wxStaticText(self, -1, "Email: ")

        self.emailInput = wxTextCtrl(self, 
                                     -1, 
                                     "",
                                     wxDefaultPosition,
                                     wxSize(300, -1))

        boxSizer.Add(notice, wxALIGN_CENTER)
        boxSizer.Add(enter, wxALIGN_CENTER)

        dataSizer = wxFlexGridSizer(2, 2, 5, 10)

        dataSizer.Add(userNameLabel)
        dataSizer.Add(self.userNameInput)

        dataSizer.Add(emailLabel)
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

        #self.SetAffirmativeId(wxID_OK)

        boxSizer.Add(buttons)

        self.SetSizer(topSizer)
        self.Fit()

        self.emailInput.SetFocus()

        EVT_BUTTON(self, wxID_OK, self.OnOk)

    def GetUserName(self):
        return self.userNameInput.GetLineText(0)

    def GetEmail(self):
        return self.emailInput.GetLineText(0)

    def Validate(self):
        # XXX Validate UserName
        user_ok = validate.validateUserName(self.GetUserName())
        email_ok = validate.validateEmail(self.GetEmail())

        if not user_ok:
            validate.warnUserName(self, self.GetUserName())

        if not email_ok:
            validate.warnEmail(self, self.GetEmail())

        return email_ok and user_ok

    def OnOk(self, event):
        if self.Validate():
            self.EndModal(wxID_OK)
