class MozUI:
    prefix = "http://localhost/~tduerig/"
    maindocbase = 'frames["mainFrame"].document'
    topdocbase = 'frames["topFrame"].document'

    def _getJSMainElem(self, name):
        return self.maindocbase + '.getElementById("' + name + '").innerHTML=window.name'
    def _getJSTopElem(self, name):
        return self.topdocbase + '.getElementById("' + name + '").innerHTML=window.name'

    def __init__(self, servio):
        self.servio = servio

    def showTick(self, sodauser):
        if not sodauser.isAnon():
            ttlstr = self._getJSMainElem("TTL")
            self.servio.send(["MOZ-JAVASCRIPT",
                      ttlstr,
                      sodauser.getTTL()])

    def updateBalance(self, sodauser):
        balance = sodauser.getBalance()

        if not sodauser.isAnon():
            balancestr = self._getJSMainElem("BALANCE")

            color = "#00FF00"
            if balance < 0:
                color = "#FF0000"

            balanceval = '<font color="' + color + '">'\
                          + str("$%0.2f" % (balance / 100.0)) + '</font>'

            self.servio.send(["MOZ-JAVASCRIPT",
                              balancestr,
                              balanceval])
        else:
            self.servio.send(["UI-OPEN",
                              self.prefix + "index.php?balance="\
                              + str(balance)])



    def logOut(self, sodauser=None):
        self.servio.send(["UI-OPEN",\
                  self.prefix + 'index.php?msg=LOGGEDOUT&balance=0'])

    def logIn(self, sodauser):
        if sodauser.isAnon():
            self.servio.send(["UI-OPEN",\
                  self.prefix + 'index.php?msg=LOGGEDOUT&balance=' +\
                  str(sodauser.getBalance())])
        else:
            self.servio.send(["UI-OPEN",\
                  self.prefix + 'index.php?msg=LOGGEDIN&login='\
                  + sodauser.getLogin() + '&balance=' +\
                  str(sodauser.getBalance()) + '&TTL=' +\
                  str(sodauser.getTTL())])

    def passwordLogin(self, login, balance, hash):
        self.servio.send(["UI-OPEN",\
              self.prefix + 'index.php?msg=PASSWORD'\
                          + '&login=' + login\
                          + '&balance=' + str(balance)\
                          + '&hash=' + hash\
                          + '&TTL=300'])


    def vendDeny(self, sodauser, note):
        if sodauser.isAnon():
            self.servio.send(['MOZ-JAVASCRIPT',
                              self._getJSTopElem("LASTACTION"),
                              note])

    def vendFail(self, sodauser):
        if sodauser.isAnon():
            self.servio.send(['MOZ-JAVASCRIPT',
                              self._getJSTopElem("LASTACTION"),
                              "ANONYMOUS VEND FAILED"])


    def vendComplete(self, sodauser, itemname):
        itemstr = itemname.replace(' ', '+')

        if sodauser.isAnon():
            self.servio.send(['MOZ-JAVASCRIPT',
                              self._getJSTopElem("LASTACTION"),
                              "ANONYMOUS VEND APPROVED"])
        else:
            self.servio.send(["UI-OPEN",
                              self.prefix + "index.php?msg=BOUGHT&login="\
                              + sodauser.getLogin()\
                              + "&balance=" + str(sodauser.getBalance())\
                              + "&item=" + itemstr\
                              + "&TTL=" + str(sodauser.getTTL())])

    def fpCount(self, sodauser, count):
        self.servio.send(['MOZ-JAVASCRIPT',
                          self._getJSMainElem("FPCOUNT"),
                          str(count) + " MORE TIME(S)"])

    def fpRead(self, sodauser, count):
        self.servio.send(['MOZ-JAVASCRIPT',
                          self._getJSTopElem("MSG"),
                          "LEARNING STATUS: PRINT READ SUCCESSFULLY"])
        self.fpCount(sodauser, count)

    def fpLearnFail(self, sodauser, msg):
        print "Ui trying to send msg " + msg
        self.servio.send(['MOZ-JAVASCRIPT',
                          self._getJSTopElem("MSG"),
                          msg])

    def fpLearnSuccess(self, sodauser, msg):
       self.logIn(sodauser) 

