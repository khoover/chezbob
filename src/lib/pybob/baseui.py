
class BaseUI:
    def __init__(self, servio):
        pass

    def showTick(self, sodauser):
        pass

    def updateBalance(self, sodauser):
        pass

    def updateTTL(self, sodauser):
        pass

    def logOut(self, sodauser=None):
        pass

    def logIn(self, sodauser):
        pass

    def passwordLogin(self, login, balance, hash):
        pass

    def vendDeny(self, sodauser, note):
        pass

    def vendFail(self, sodauser):
        pass

    def vendComplete(self, sodauser, itemname, itemprice=0):
        pass

    def fpRead(self, sodauser, count):
        pass

    def fpLearnFail(self, sodauser, count, msg):
        pass

    def fpLearnSuccess(self, sodauser, msg):
        pass

