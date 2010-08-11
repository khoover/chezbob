import wx
from chez_panel import *

class PasswordPanel(ChezPanel):
    def __init__(self, parent, ID, pos, size):
        ChezPanel.__init__(self, parent, ID, pos, size)

        marginHeight = self.GetSize().GetHeight() / 3

        passwordPrompt = wx.StaticText(
                                    self,
                                    -1,
                                    "Enter your password: ",
                                    style=wx.ALIGN_RIGHT
                                    )

        self.passwordInput = wx.TextCtrl(
                                    self,
                                    -1,
                                    "",
                                    wx.DefaultPosition,
                                    wx.Size(200, -1),
                                    wx.TE_PROCESS_ENTER | wx.TE_PASSWORD
                                    )

        vSizer = wx.BoxSizer(wx.VERTICAL)

        passwordSizer = wx.BoxSizer(wx.HORIZONTAL)
        passwordSizer.Add(passwordPrompt, 0, wx.ALIGN_RIGHT)
        passwordSizer.Add(self.passwordInput, 1, wx.ALIGN_LEFT)

        vSizer.AddSpacer((-1, marginHeight))
        vSizer.Add(passwordSizer, 0, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 20)

        self.SetSizer(vSizer)

    def Show(self, show=True):
        if show:
            self.passwordInput.SetFocus()

        ChezPanel.Show(self, show)

    def Clear(self):
        self.passwordInput.Clear()

    def GetPassword(self):
        return self.passwordInput.GetLineText(0)
