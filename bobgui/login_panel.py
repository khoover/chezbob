from chez_panel import *

class LoginPanel(ChezPanel):
    def __init__(self, parent, ID, pos, size):
        ChezPanel.__init__(self, parent, ID, pos, size)

        marginHeight = self.GetSize().GetHeight() / 3

        welcomeMessage = wxStaticText(
                                      self,
                                      -1,
                                      "Welcome to ChezBob!",
                                      style=wxALIGN_CENTER | wxEXPAND
                                      )

        subTextMessage = wxStaticText(
                                      self,
                                      -1,
      "To create an account, enter your desired username.  If it doesn't \
belong to someone else, you will be prompted to create a new one",
                                      style=wxALIGN_CENTER | wxEXPAND
                                      )
        subTextMessage.Wrap(self.GetSize().GetWidth() * 2/3)

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

        welcomeSizer = wxBoxSizer(wxHORIZONTAL)

        welcomeSizer.AddSpacer((-1, marginHeight), 0)

        welcomeSizer.Add(welcomeMessage, 
                         1, 
                        wxEXPAND | wxALIGN_CENTER | wxTOP, 
                        20)

        welcomeSizer.AddSpacer((-1, marginHeight), 0)

        vSizer.Add(welcomeSizer, 0, wxEXPAND)

        vSizer.Add(loginSizer, 0, wxALIGN_CENTER | wxEXPAND | wxALL, 20)

        vSizer.Add(subTextMessage, 0, wxEXPAND | wxTOP, marginHeight / 2)

        self.SetSizer(vSizer)

    def Show(self, show=true):
        if show:
            self.loginInput.SetFocus()

        ChezPanel.Show(self, show)

    def Clear(self):
        self.loginInput.Clear()

    def GetLogin(self):
        return self.loginInput.GetLineText(0)
