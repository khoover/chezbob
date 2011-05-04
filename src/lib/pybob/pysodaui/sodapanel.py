from wxPython.wx import *
from pyui.config import *

sodaBgImage = wxImage(sodaBgImagePath)
sodaBgImageBitmap = None

class SodaPanel(wxPanel):
    leftBarWidth = 150
    topBarHeight = 40
    topLineHeight = 40
    botLineHeight = 40
    buttonSpacing = 2
    leftBarColour = 'ORANGE'

    def __init__(self, parent, ID, pos, size):
        wxPanel.__init__(self, parent, ID, pos, size)

        # Hackomatic
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetForegroundColour(parent.GetForegroundColour())

        self.parent = parent

        global sodaBgImageBitmap
        if sodaBgImageBitmap is None:
            sodaBgImageBitmap = sodaBgImage.ConvertToBitmap()

        wxStaticBitmap(self, -1, sodaBgImageBitmap)

        # Build Generic Setup
        self.VertSizer = wxBoxSizer(wxVERTICAL)

        # Top Padding
        self.TopSpaceSizer = wxBoxSizer(wxHORIZONTAL)

        self.TopSpaceSizer.AddSpacer(wxSize(self.leftBarWidth,
                                            self.topBarHeight))

        self.TopSpaceSizer.AddSpacer(wxSize(30, -1)) # Move past the curve

        self.StatusLabel = wxStaticText(self, -1, "Status: ",
                                        size = wxSize(-1, self.topBarHeight),
                                        style = wxALIGN_LEFT)

        self.TopSpaceSizer.Add(self.StatusLabel, 0)

        self.StatusTextLabel = wxStaticText(self, -1, "Idle")


        self.TopSpaceSizer.Add(self.StatusTextLabel, 1)

        self.VertSizer.Add(self.TopSpaceSizer)

        self.VertSizer.AddSpacer(wxSize(-1, self.topLineHeight))

        self.MainSizer = wxBoxSizer(wxHORIZONTAL)

        self.LeftBarSizer = wxBoxSizer(wxVERTICAL)

        leftBarTopSpacer = wxStaticText(self, 
                                  -1, 
                                  "",
                                  wxDefaultPosition, 
                                  wxSize(self.leftBarWidth,25))
        self.LeftBarSizer.Add(leftBarTopSpacer)

        buttonTopSpacer = wxPanel(self, -1, 
                        size=wxSize(self.leftBarWidth,
                        self.buttonSpacing))
        buttonTopSpacer.SetBackgroundColour('BLACK')
        self.LeftBarSizer.Add(buttonTopSpacer)

        self.ContentSizer = wxBoxSizer(wxVERTICAL)
        self.ResetContentSizer()


        self.MainSizer.Add(self.LeftBarSizer)
        self.MainSizer.Add(self.ContentSizer)

        self.VertSizer.Add(self.MainSizer)

        self.SetSizer(self.VertSizer)

    def ResetContentSizer(self):
        self.ContentSizer.Clear()

        # Force the content sizer as wide as the area.
        self.ContentSizer.AddSpacer(
                wxSize(self.GetContentWidth(), 0))

    def GetContentWidth(self):
        return self.GetSize().GetWidth() - self.leftBarWidth


    def AddLeftButton(self, Widget):
        """
        Wraps all the parameters for adding a button to the left bar.
        """

        self.LeftBarSizer.Add(
                    Widget,
                    1, # re-proportion
                    wxALIGN_CENTER_HORIZONTAL
                    )

        buttonSpacer = wxPanel(self, -1, 
                        size=wxSize(self.leftBarWidth,
                        self.buttonSpacing))
        buttonSpacer.SetBackgroundColour('BLACK')

        self.LeftBarSizer.Add(buttonSpacer)

    def AddLeftSpacer(self, size):
        self.LeftBarSizer.AddSpacer(size)

    def SetStatusText(self, text, colour='WHITE'):
        self.StatusTextLabel.SetLabel(text)
        self.StatusTextLabel.SetForegroundColour(colour)
