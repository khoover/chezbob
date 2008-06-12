from wxPython.wx import *
from pyui.config import *
from pyui.sodapanel import *
from pyui.sodabutton import *
from pyui.stats import *

class SodaLoginIdlePanel(SodaPanel):

    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.idlePanelSizer = wxBoxSizer(wxVERTICAL)

        loginButton = SodaButton(self, ID_LOGIN, 'LOGIN')

        self.AddLeftButton(loginButton)

        self.SetStatusText("Idle")

        self.statsPanel = None


    def MakeSodaStatsPanel(self):
        if self.statsPanel is not None:
            self.statsPanel.Destroy()

        self.statsPanel = SodaIdleSodaStatsPanel(self, -1,
                wxDefaultPosition, wxSize(self.GetContentWidth(), -1))

        self.ResetContentSizer()
        self.ContentSizer.Add(self.statsPanel)


        self.ContentSizer.Layout()
