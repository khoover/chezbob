from wxPython.wx import *
from config import *
from sodapanel import *
from sodabutton import *

class SodaFPPanel(SodaPanel):
    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.AddLeftButton(
                SodaButton(
                    self,
                    ID_CANCEL, 
                    'CANCEL'
                    )
                         )

        self.StatusLabel = wxStaticText(
                self,
                -1,
                ""
                )
        self.Instructions = wxStaticText(
                self,
                -1,
                "PLEASE TRAIN YOUR\nFINGERPRINT ON THE\nREADER BELOW...",
                style=wxALIGN_CENTER
                )
        self.Instructions.SetForegroundColour(SodaOrange)

        instrfont = self.Instructions.GetFont()
        instrfont.SetPointSize(40)
        self.Instructions.SetFont(instrfont)


        self.UpperSizer = wxBoxSizer(wxHORIZONTAL)
        self.UpperLeftSizer = wxBoxSizer(wxVERTICAL)

        self.UpperLeftSizer.Add(self.StatusLabel)
        self.UpperLeftSizer.Add(self.Instructions)

        self.UpperSizer.Add(self.UpperLeftSizer, proportion=1)
        self.UpperSizer.AddSpacer(wxSize(300,-1))

        self.CountPrompt = wxStaticText(
                self,
                -1,
                "Please put your finger on the reader below."
                )
        # We leave these here just in case they're referenced somewhere. They
        # aren't added to the sizer, so they'll never show up.
        self.CountNumber = wxStaticText(
                self,
                -1,
                "3"
                )
        self.CountPostPrompt = wxStaticText(
                self,
                -1,
                " more time(s)"
                )

        self.CountSizer = wxBoxSizer(wxHORIZONTAL)
        self.CountSizer.Add(self.CountPrompt)
        #self.CountSizer.Add(self.CountNumber)
        #self.CountSizer.Add(self.CountPostPrompt)

        self.TimerLabel = wxStaticText(
                self,
                -1,
                "TimerLabel"
                )

        self.ContentSizer.Add(self.UpperSizer)
        self.ContentSizer.Add(self.CountSizer)
        self.ContentSizer.Add(self.TimerLabel)

        self.UpperSizer.Layout()


    def SetCount(self, count):
        pass
        #self.CountNumber.SetLabel(str(count))
        #self.CountSizer.Layout()

    def SetMessage(self, message):
        self.StatusLabel.SetLabel(message)
        self.UpperSizer.Layout()

    def SetTTL(self, ttl):
        self.TimerLabel.SetLabel("Timeout in " + str(ttl) + " seconds")

    def Clear(self):
        self.StatusLabel.SetLabel("")
        self.TimerLabel.SetLabel("")
