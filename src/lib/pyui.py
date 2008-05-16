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

    def fpRead(self, sodauser, count):
        self.servio.send(["UI-FP-NOTICE",
                          count,
                          "Print Read Successfully",
                          0])

    def fpLearnFail(self, sodauser, count, msg):
        self.servio.send(["UI-FP-NOTICE",
                          count,
                          "LEARNING FAILED: " + msg,
                          0])

    def fpLearnSuccess(self, sodauser, msg):
        self.servio.send(["UI-FP-NOTICE",
                          0,
                          "LEARNING SUCCEEDED: " + msg,
                          1])
