from wxPython.wx import *
from config import *
from sodapanel import *
from sodabutton import *
from stats import *
import random
import traceback
import sys

class SodaLoginIdlePanel(SodaPanel):

    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.idlePanelSizer = wxBoxSizer(wxVERTICAL)

        loginButton = SodaButton(self, ID_LOGIN, 'LOGIN')

        self.AddLeftButton(loginButton)

        self.SetStatusText("Idle")

        self.statsPanel = None

        self.random = random.Random()

    def MakeSodaStatsPanel(self):
        if self.statsPanel is not None:
            self.statsPanel.Destroy()

        try:
            r = self.random.choice([0,1])

            if r == 0:
                self.statsPanel = SodaIdleSodaStatsPanel(self, -1,
                        wxDefaultPosition, wxSize(self.GetContentWidth(), -1))
            elif r == 1:
                self.statsPanel = SodaIdleWallOfShamePanel(self, -1,
                        wxDefaultPosition, wxSize(self.GetContentWidth(), -1))
            else:
                raise "Invalid Choice"

            self.ResetContentSizer()
            self.ContentSizer.Add(self.statsPanel)
        except Exception, e:
            print "Failed to make stats panel", e
            traceback.print_tb(sys.exc_info()[2])



        self.ContentSizer.Layout()
