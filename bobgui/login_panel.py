from chez_panel import *

class LoginPanel(ChezPanel):
    def __init__(self, parent, ID, pos, size):
        ChezPanel.__init__(self, parent, ID, pos, size)

        marginHeight = self.GetSize().GetHeight() / 3

        loginPrompt = wxStaticText(
                                    self,
                                    -1,
                                    "Enter your username: ",
                                    style=wxALIGN_LEFT
                                    )

        self.loginInput = wxTextCtrl(
                                    self,
                                    -1,
                                    "",
                                    wxDefaultPosition,
                                    wxSize(200, -1),
                                    wxTE_PROCESS_ENTER
                                    )

        vSizer = wxBoxSizer(wxVERTICAL)

        loginSizer = wxBoxSizer(wxHORIZONTAL)

        loginSizer.Add(loginPrompt, 0, wxALIGN_RIGHT)
        loginSizer.Add(self.loginInput, 1, wxALIGN_LEFT)

        vSizer.AddSpacer((-1, marginHeight))
        vSizer.Add(loginSizer, 0, wxALIGN_CENTER | wxEXPAND | wxALL, 20)

        self.SetSizer(vSizer)

    def Show(self, show=true):
        if show:
            self.loginInput.SetFocus()

        ChezPanel.Show(self, show)

    def Clear(self):
        self.loginInput.Clear()

    def GetLogin(self):
        return self.loginInput.GetLineText(0)
