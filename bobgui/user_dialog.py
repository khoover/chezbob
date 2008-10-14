from wxPython.wx import *

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

