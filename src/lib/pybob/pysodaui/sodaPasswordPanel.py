from wxPython.wx import *
from config import *
from sodapanel import *
from sodabutton import *
from keyboard import *

class SodaPasswordPanel(SodaPanel):
    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)


        self.AddLeftButton(SodaButton(self, 
            ID_DOPASSWORD, 
            'Login'))

        self.AddLeftButton(SodaButton(self,
            ID_CANCEL,
            'Cancel'))


        passwordInfoSizer = wxBoxSizer(wxHORIZONTAL)

        self.passwordLabel = wxStaticText(
                self,
                -1,
                "Password:",
                style=wxALIGN_RIGHT
                )

        passwordInfoSizer.Add(self.passwordLabel, 1, wxALIGN_CENTER)

        self.passwordInput = wxTextCtrl(
                self, 
                -1,
                "",
                wxDefaultPosition,
                wxSize(200, -1), # XXX
                wxPASSWORD
                )

        passwordInfoSizer.Add(self.passwordInput, 1, wxALIGN_CENTER)

        self.ContentSizer.Add(passwordInfoSizer)
        self.ContentSizer.AddSpacer(wxSize(50,50))
        self.ContentSizer.Add(SodaKeyBoard(self,
            -1, wxDefaultPosition, wxSize(400, 400), self.passwordInput), 
            flag=wxALIGN_CENTER, proportion=1)

    def GetPassword(self):
        return self.passwordInput.GetLineText(0)

    def Clear(self):
        self.passwordInput.Clear()
