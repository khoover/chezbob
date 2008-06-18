from wxPython.wx import *
from pyui.config import *
import PHPUnserialize


class SodaIdleStatsPanel(wxPanel):
    def __init__(self, parent, ID, pos, size):
        wxPanel.__init__(self, parent, ID, pos, size)

class BarGraphPanel(SodaIdleStatsPanel):
    def __init__(self, parent, ID, pos, size, stats_list, min, max):
        SodaIdleStatsPanel.__init__(self, parent, ID, pos, size)

        font = self.GetFont()
        font.SetPointSize(SodaStatsFontSize)

        self.statsSizer = wxBoxSizer(wxVERTICAL)
        self.SetSizer(self.statsSizer)
        self.SetBackgroundColour(parent.GetBackgroundColour())

        barpad = 20 * len(str(min)) 
        padding = 10
        # Column width
        cw = size.GetWidth() - padding * 2

        for val in stats_list:
            sizer = wxBoxSizer(wxHORIZONTAL)

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
            # This spacing/padding comes out different on different
            # machines.
            number.SetFont(font)

            numberPanel.SetBackgroundColour(SodaLightGreen)
            numberPanel.SetSizer(numberSizer)

            numberSizer.Add(number, proportion=0)

            sizer.AddSpacer(wxSize(padding, -1))
            sizer.Add(label)
            sizer.Add(numberPanel)

            self.statsSizer.Add(sizer)
            self.statsSizer.AddSpacer(wxSize(1, 1))

# This could probably be generalized a little better
class SodaIdleSodaStatsPanel(BarGraphPanel):
    sodaStatsPath = "/var/soda/stockcount.psr"
    unserializer = PHPUnserialize.PHPUnserialize()

    def __init__(self, parent, ID, pos, size):
        file = open(self.sodaStatsPath, "r")
        stats = self.unserializer.unserialize(file.read())
        file.close()

        stats_keys = filter(lambda x: x != "r10", stats.keys())
        stats_list = [(stats[key]["sold"], stats[key]["name"]) for key in stats_keys]
        stats_list.sort(cmp=lambda x,y:cmp(y,x))

        min = stats_list[-1][0]
        max = stats_list[0][0]

        BarGraphPanel.__init__(self, parent, ID, pos, size, stats_list, min, max)

