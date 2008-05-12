import pyui
import mozui

class UnionUI:
    def __init__(self, servio):
        self.mozui = mozui.MozUI(servio)
        self.pyui = pyui.PyUI(servio)

    def showTick(self, sodauser):
        self.mozui.showTick(sodauser)
        self.mozui.updateBalance(sodauser)

    def updateBalance(self, sodauser):
        self.mozui.updateBalance(sodauser)
        self.pyui.updateBalance(sodauser)

    def logOut(self, sodauser=None):
        self.mozui.logOut(sodauser)
        self.pyui.logOut(sodauser)

    def logIn(self, sodauser):
        self.mozui.logIn(sodauser)
        self.pyui.logIn(sodauser)

    def passwordLogin(self, login, balance, hash):
        self.mozui.passwordLogin(login, balance, hash)
        self.pyui.passwordLogin(login, balance, hash)

    def vendDeny(self, sodauser, note):
        self.mozui.vendDeny(sodauser, note)
        self.pyui.vendDeny(sodauser.note)

    def vendFail(self, sodauser):
        self.mozui.vendFail(sodauser)
        self.pyui.vendFail(sodauser)

    def vendComplete(self, sodauser, itemname, itemprice=0):
        self.mozui.vendComplete(sodauser, itemname)
        self.pyui.vendComplete(sodauser, itemname, itemprice)

    def fpCount(self, sodauser, count):
        self.mozui.fpCount(sodauser, count)
        self.pyui.fpCount(sodauser, count)

    def fpRead(self, sodauser, count):
        self.mozui.fpRead(sodauser, count)
        self.pyui.fpRead(sodauser, count)

        self.fpCount(sodauser, count)

    def fpLearnFail(self, sodauser, msg):
        self.mozui.fpLearnFail(sodauser, msg)
        self.pyui.fpLearnFail(sodauser, msg)

    def fpLearnSuccess(self, sodauser, msg):
        self.logIn(sodauser) 

