import baseui

class PyUI(baseui.BaseUI):
    def __init__(self, servio):
        self.servio = servio

    def updateBalance(self, sodauser):
        balance = sodauser.getBalance()
        self.servio.send(["UI-BALANCE", str(balance)])
        self.updateTTL(sodauser)

    def updateTTL(self, sodauser):
        ttl = sodauser.getTTL()
        self.servio.send(["UI-TTL", str(ttl)])


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

    def fpRead(self, count):
        self.servio.send(["UI-FP-NOTICE",
                          count,
                          "Print Read Successfully",
                          0])

    def fpReadFail(self, msg):
        print "sending message"
        self.servio.send(["UI-FP-NOTICE",
                          0,
                          msg,
                          0])

    def fpLearnFail(self, msg):
        self.servio.send(["UI-FP-NOTICE",
                          0, #This may be displayed it is no longer used
                          "LEARNING FAILED: " + msg,
                          0])

    def fpLearnSuccess(self, msg):
        self.servio.send(["UI-FP-NOTICE",
                          0,
                          "LEARNING SUCCEEDED: " + msg,
                          1])
