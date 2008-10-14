from chez_panel import *

class LoginPanel(ChezPanel):
    def __init__(self, parent, ID, pos, size):
        ChezPanel.__init__(self, parent, ID, pos, size)

        marginWidth = self.GetSize().GetWidth() / 3
        marginHeight = self.GetSize().GetHeight() / 3

        loginPrompt = wxStaticText(
                                    self,
                                    -1,
                                    "Enter your username: "
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

        loginSizer.Add(wxPanel(self, -1, size=wxSize(marginWidth, -1)))
        loginSizer.Add(loginPrompt, wxALIGN_LEFT)
        loginSizer.Add(self.loginInput, wxALIGN_RIGHT)
        loginSizer.Add(wxPanel(self, -1, size=wxSize(marginWidth, -1)))

        vSizer.Add(wxPanel(self, -1, size=wxSize(-1,marginHeight)))

        vSizer.Add(loginSizer, wxALIGN_CENTER)

        vSizer.Add(wxPanel(self, -1, size=wxSize(-1,marginHeight)))

        self.SetSizer(vSizer)

    def Show(self, show=true):
        if show:
            self.loginInput.SetFocus()

        ChezPanel.Show(self, show)

    def Clear(self):
        self.loginInput.Clear()

    def GetLogin(self):
        return self.loginInput.GetLineText(0)
