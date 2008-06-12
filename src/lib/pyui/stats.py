from wxPython.wx import *
from pyui.config import *
import PHPUnserialize

class SodaIdleStatsPanel(wxPanel):
    def __init__(self, parent, ID, pos, size):
        wxPanel.__init__(self, parent, ID, pos, size)

# This could probably be generalized a little better
class SodaIdleSodaStatsPanel(SodaIdleStatsPanel):
    sodaStatsPath = "/var/soda/stockcount.psr"
    unserializer = PHPUnserialize.PHPUnserialize()

    def __init__(self, parent, ID, pos, size):
        SodaIdleStatsPanel.__init__(self, parent, ID, pos, size)

        file = open(self.sodaStatsPath, "r")
        stats = self.unserializer.unserialize(file.read())
        file.close()

        self.statsSizer = wxBoxSizer(wxVERTICAL)
        self.SetSizer(self.statsSizer)
        self.SetBackgroundColour(parent.GetBackgroundColour())

        stats_keys = filter(lambda x: x != "r10", stats.keys())
        stats_list = [(stats[key]["sold"], stats[key]["name"]) for key in stats_keys]
        stats_list.sort(cmp=lambda x,y:cmp(y,x))

        padding = 10
        cw = size.GetWidth() - padding * 2

        max = stats_list[0][0]
        min = stats_list[-1][0]

        font = self.GetFont()
        font.SetPointSize(SodaStatsFontSize)

        for val in stats_list:
            sizer = wxBoxSizer(wxHORIZONTAL)

            barpad = 20 * len(str(min)) 
            w = (cw - barpad) * 0.75 * (val[0] - min) / max + barpad

            label = wxStaticText(self,   
                                       -1, 
                                       val[1],
                                       wxDefaultPosition,
                                       wxSize(cw * 0.25, -1))

            label.SetForegroundColour(SodaOrange)
            label.SetFont(font)

            numberSizer = wxBoxSizer(wxVERTICAL)

            numberPanel = wxPanel(self, -1)
            number = wxStaticText(numberPanel,   
                                       -1, 
                                       str(val[0]),
                                       wxDefaultPosition,
                                       wxSize(w, SodaStatsFontSize*1.5),
                                       style=wxALIGN_RIGHT)
            number.SetFont(font)
    
            numberPanel.SetBackgroundColour(SodaLightGreen)
            numberPanel.SetSizer(numberSizer)

            numberSizer.Add(number, proportion=0)

            sizer.AddSpacer(wxSize(padding, -1))
            sizer.Add(label)
            sizer.Add(numberPanel)

            self.statsSizer.Add(sizer)
