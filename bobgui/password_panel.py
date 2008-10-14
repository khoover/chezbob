
from chez_panel import *

class PasswordPanel(ChezPanel):
    def __init__(self, parent, ID, pos, size):
        ChezPanel.__init__(self, parent, ID, pos, size)

        marginWidth = self.GetSize().GetWidth() / 3
        marginHeight = self.GetSize().GetHeight() / 3

        passwordPrompt = wxStaticText(
                                    self,
                                    -1,
                                    "Enter your password: "
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

        passwordSizer.Add(wxPanel(self, -1, size=wxSize(marginWidth, -1)))
        passwordSizer.Add(passwordPrompt, wxALIGN_LEFT)
        passwordSizer.Add(self.passwordInput, wxALIGN_RIGHT)
        passwordSizer.Add(wxPanel(self, -1, size=wxSize(marginWidth, -1)))

        vSizer.Add(wxPanel(self, -1, size=wxSize(-1,marginHeight)))

        vSizer.Add(passwordSizer, wxALIGN_CENTER)

        vSizer.Add(wxPanel(self, -1, size=wxSize(-1,marginHeight)))

        self.SetSizer(vSizer)

    def Show(self, show=true):
        if show:
            self.passwordInput.SetFocus()

        ChezPanel.Show(self, show)

    def Clear(self):
        self.passwordInput.Clear()

    def GetPassword(self):
        return self.passwordInput.GetLineText(0)
