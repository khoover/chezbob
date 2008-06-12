from wxPython.wx import *
from pyui.config import *
from pyui.sodapanel import *
from pyui.sodabutton import *
from pyui.keyboard import *

class SodaLoginPanel(SodaPanel):
    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.AddLeftButton(SodaButton(self,
            ID_DOLOGIN, 
            'LOGIN'))

        self.AddLeftButton(SodaButton(self,
            ID_CANCEL,
            'CANCEL'))

        loginInfoSizer = wxBoxSizer(wxHORIZONTAL)

        loginLabel = wxStaticText(
                self,
                -1,
                "Login: ",
                style = wxALIGN_RIGHT
                )

        loginInfoSizer.Add(loginLabel, 1, wxALIGN_CENTER)

        self.loginInput = wxTextCtrl(
                self, 
                -1,
                "",
                wxDefaultPosition,
                wxSize(200, -1) # XXX
                )

        loginInfoSizer.Add(self.loginInput, 1, wxALIGN_CENTER)

        self.ContentSizer.Add(loginInfoSizer)

        self.ContentSizer.AddSpacer(wxSize(50,50))
        self.ContentSizer.Add(SodaKeyBoard(self,
            -1, wxDefaultPosition, wxSize(400, 400), self.loginInput),
            flag=wxALIGN_CENTER, proportion=1)

        self.SetStatusText('Authenticating', 'YELLOW')

    def GetLogin(self):
        return self.loginInput.GetLineText(0)

    def Clear(self):
        self.loginInput.Clear()
