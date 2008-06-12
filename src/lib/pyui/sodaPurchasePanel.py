from wxPython.wx import *
from pyui.config import *
from pyui.sodapanel import *
from pyui.sodabutton import *

def monetize(val):
    return "$%0.2f" % (int(val) / 100.0)

class SodaPurchasePanel(SodaPanel):
    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.AddLeftButton(
                SodaButton(
                    self,
                    ID_LOGOUT, 
                    'Logout'
                    )
                   )

        self.AddLeftSpacer(wxSize(-1, 200))

        self.AddLeftButton(
                SodaButton(
                    self,
                    ID_FPLEARN,
                    'Learn FP'
                    )
                   )

        self.UserSalutations = wxStaticText(
                self,
                -1,
                "Hello "
                )
        self.UserLabel = wxStaticText(
                self,
                -1,
                "UserLabel",
                style=wxALIGN_LEFT
                )
        self.UserLabel.SetForegroundColour(SodaDarkOrange)

        self.UserLabelComma = wxStaticText(
                self,
                -1,
                ","
                )

        self.UserSizer = wxBoxSizer(wxHORIZONTAL)

        self.UserSizer.Add(self.UserSalutations)
        self.UserSizer.Add(self.UserLabel)
        self.UserSizer.Add(self.UserLabelComma)


        self.BalanceText = wxStaticText(
                self,
                -1,
                "You have a Balance of "
                )
        self.BalanceLabel = wxStaticText(
                self,
                -1,
                "BalanceLabel"
                )

        self.BalanceSizer = wxBoxSizer(wxHORIZONTAL)
        self.BalanceSizer.Add(self.BalanceText)
        self.BalanceSizer.Add(self.BalanceLabel)

        self.TimerLabel = wxStaticText(
                self,
                -1,
                "TimerLabel"
                )



        self.ContentSizer.Add(self.UserSizer)
        self.ContentSizer.Add(self.BalanceSizer)
        self.ContentSizer.Add(self.TimerLabel)

        self.purchaseLog = wxStaticText(
                                        self,
                                        -1,
                                        "",
                                        wxDefaultPosition,
                                        wxSize(400, -1)
                                        )

        self.ContentSizer.Add(self.purchaseLog)

    def SetUser(self, user):
        self.UserLabel.SetLabel(user)
        self.UserSizer.Layout()

    def SetBalance(self, balance):
        self.BalanceLabel.SetLabel(str(monetize(balance)))

    def SetTTL(self, ttl):
        self.TimerLabel.SetLabel("Timeout in " + str(ttl) + " seconds")

    def AddLog(self, message):
        self.purchaseLog.SetLabel(self.purchaseLog.GetLabel() + "\n" + message)

    def Clear(self):
        self.UserLabel.SetLabel("")
        self.BalanceLabel.SetLabel("")
        self.TimerLabel.SetLabel("")
        self.purchaseLog.SetLabel("")
