
from chez_panel import *

class PasswordPanel(ChezPanel):
    def __init__(self, parent, ID, pos, size):
        ChezPanel.__init__(self, parent, ID, pos, size)

        marginHeight = self.GetSize().GetHeight() / 3

        passwordPrompt = wxStaticText(
                                    self,
                                    -1,
                                    "Enter your password: ",
                                    style=wxALIGN_RIGHT
                                    )

        self.passwordInput = wxTextCtrl(
                                    self,
                                    -1,
                                    "",
                                    wxDefaultPosition,
                                    wxSize(200, -1),
                                    wxTE_PROCESS_ENTER | wxTE_PASSWORD
                                    )

        vSizer = wxBoxSizer(wxVERTICAL)

        passwordSizer = wxBoxSizer(wxHORIZONTAL)
        passwordSizer.Add(passwordPrompt, 0, wxALIGN_RIGHT)
        passwordSizer.Add(self.passwordInput, 1, wxALIGN_LEFT)

        vSizer.AddSpacer((-1, marginHeight))
        vSizer.Add(passwordSizer, 0, wxALIGN_CENTER | wxALL | wxEXPAND, 20)

        self.SetSizer(vSizer)

    def Show(self, show=true):
        if show:
            self.passwordInput.SetFocus()

        ChezPanel.Show(self, show)

    def Clear(self):
        self.passwordInput.Clear()

    def GetPassword(self):
        return self.passwordInput.GetLineText(0)
