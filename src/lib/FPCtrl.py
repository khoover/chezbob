import servio

class FPCtrl:
    def __init__(self, bus):
        self.bus = bus
        self.FPServVL = self.bus.getVarList("FPSERV")

    def doLoginMode(self):
        self.FPServVL.set("visible", None, "0")
        self.FPServVL.set("winx", None, "1")
        self.FPServVL.set("winy", None, "199")
        self.FPServVL.set("auto_hide", None, "1")
        self.FPServVL.set("auto_show", None, "1")
        self.FPServVL.set("capture_match", None, "1")

    def doDisable(self):
        self.FPServVL.set("visible", None, "0")
        self.FPServVL.set("auto_show", None, "0")
        self.FPServVL.set("capture_match", None, "0")

    def doLearnMode(self):
        self.FPServVL.set("winx", None, "500")
        self.FPServVL.set("winy", None, "130")
        self.FPServVL.set("auto_hide", None, "0")
        self.FPServVL.set("visible", None, "1")
