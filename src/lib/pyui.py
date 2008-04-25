class PyUI:
    def __init__(self, servio):
        self.servio = servio

    def updateBalance(self, sodauser):
        balance = sodauser.getBalance()
        self.servio.send(["UI-BALANCE", str(balance)])

    def logOut(self, sodauser=None):
        self.servio.send(["UI-LOGGEDOUT"])

    def logIn(self, sodauser):
        anon = 0
        if sodauser.isAnon():
            anon = 1;

        self.servio.send(["UI-LOGGEDIN",
                          sodauser.getLogin(),
                          sodauser.getBalance(),
                          sodauser.getTTL(),
                          anon])

    def passwordLogin(self, login, balance, hash):
        self.servio.send(["UI-PASSWORD",
                          login,
                          balance,
                          hash,
                          3,
                          30])

    def vendDeny(self, sodauser, note):
        self.servio.send(["UI-NOTICE", note, 'RED'])

    def vendFail(self, sodauser):
        self.servio.send(["UI-NOTICE", "VEND FAILED", 'RED'])

    def vendComplete(self, sodauser, itemname, itemprice):
        self.servio.send(["UI-BOUGHT",
                          itemname,
                          itemprice,
                          sodauser.getBalance(),
                          sodauser.getTTL()])

    def fpCount(self, sodauser, count):
        pass
        # TODO
        self.servio.send(['MOZ-JAVASCRIPT',
                          self._getJSMainElem("FPCOUNT"),
                          str(count) + " MORE TIME(S)"])

    def fpRead(self, sodauser, count):
        pass
        # TODO

    def fpLearnFail(self, sodauser, msg):
        pass
        #TODO

    def fpLearnSuccess(self, sodauser, msg):
        pass
        #TODO -- Login?
