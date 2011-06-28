from wxPython.wx import *

from sodapanel import *

class SodaButton(wxButton):
    def __init__(self, parent, ID, Text, font_size=45):
        wxButton.__init__(self, parent, ID, Text,
                size=wxSize(SodaPanel.leftBarWidth, -1))

        # Hackomatic
        self.SetBackgroundColour(SodaButtonColor)
        self.SetForegroundColour(SodaButtonTextColor)

        font = self.GetFont()
        font.SetPointSize(font_size)
        self.SetFont(font)
