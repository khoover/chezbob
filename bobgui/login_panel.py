import wx
from chez_panel import *

class LoginPanel(ChezPanel):
    def __init__(self, parent, ID, pos, size):
        ChezPanel.__init__(self, parent, ID, pos, size)

        marginHeight = self.GetSize().GetHeight() / 3

        welcomeMessage = wx.StaticText(
                                      self,
                                      -1,
                                      "Welcome to ChezBob!",
                                      style=wx.ALIGN_CENTER | wx.EXPAND
                                      )

        subTextMessage = wx.StaticText(
                                      self,
                                      -1,
      "To create an account, enter your desired username.  If it doesn't \
belong to someone else, you will be prompted to create a new one",
                                      style=wx.ALIGN_CENTER | wx.EXPAND
                                      )
        subTextMessage.Wrap(self.GetSize().GetWidth() * 2/3)

        loginPrompt = wx.StaticText(
                                    self,
                                    -1,
                                    "Enter your username: ",
                                    style=wx.ALIGN_LEFT
                                    )

        self.loginInput = wx.TextCtrl(
                                    self,
                                    -1,
                                    "",
                                    wx.DefaultPosition,
                                    wx.Size(200, -1),
                                    wx.TE_PROCESS_ENTER
                                    )

        vSizer = wx.BoxSizer(wx.VERTICAL)

        loginSizer = wx.BoxSizer(wx.HORIZONTAL)

        loginSizer.Add(loginPrompt, 0, wx.ALIGN_RIGHT)
        loginSizer.Add(self.loginInput, 1, wx.ALIGN_LEFT)

        welcomeSizer = wx.BoxSizer(wx.HORIZONTAL)

        welcomeSizer.AddSpacer((-1, marginHeight), 0)

        welcomeSizer.Add(welcomeMessage, 
                         1, 
                        wx.EXPAND | wx.ALIGN_CENTER | wx.TOP, 
                        20)

        welcomeSizer.AddSpacer((-1, marginHeight), 0)

        vSizer.Add(welcomeSizer, 0, wx.EXPAND)

        vSizer.Add(loginSizer, 0, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 20)

        vSizer.Add(subTextMessage, 0, wx.EXPAND | wx.TOP, marginHeight / 2)

        self.SetSizer(vSizer)

    def Show(self, show=True):
        if show:
            self.loginInput.SetFocus()

        ChezPanel.Show(self, show)

    def Clear(self):
        self.loginInput.Clear()

    def GetLogin(self):
        return self.loginInput.GetLineText(0)
