#!/usr/bin/python

# IN PROGRESS
# export PYTHONPATH=`pwd`/../lib

# Messages:
# UI-LOGGEDIN | user | balance | ttl | anonymous [01]
# - Go to the login screen
# UI-PASSWORD | user | balance | hash | tries | ttl
# - Go to the password query screen
# UI-BOUGHT   | item | price | balance | ttl
# - Notify the user of a purchase
# UI-TTL      | ttl
# - Reset the TTL
# UI-BALANCE balance
# - Set the balance
# UI-LOGGEDOUT
# - Return to Login-Idle Screen
# UI-NOTICE | notice | color
# - Issue a notice to a logged in user

from wxPython.wx import *
import servio
import threading
import wx.lib.newevent
import crypt

ID_LOGOUT  = 102
ID_LOGIN   = 103
ID_DOLOGIN = 104
ID_DOPASSWORD = 105
ID_KEYBOARD   = 106
ID_CANCEL     = 107

STATE_LOGIN_IDLE = 1
STATE_LOGIN      = 2
STATE_PASSWORD   = 3
STATE_PURCHASE   = 4

LogoutEvent, EVT_LOGOUT_EVENT = wx.lib.newevent.NewEvent()
LoginEvent, EVT_LOGIN_EVENT = wx.lib.newevent.NewEvent()
PasswordEvent, EVT_PASSWORD_EVENT = wx.lib.newevent.NewEvent()
BoughtEvent, EVT_BOUGHT_EVENT = wx.lib.newevent.NewEvent()
TtlEvent, EVT_TTL_EVENT = wx.lib.newevent.NewEvent()
BalanceEvent, EVT_BALANCE_EVENT = wx.lib.newevent.NewEvent()

bus = None

def urldecode(url):
    "Return a dict of the variables encoded in a GET request"
    vars = url[url.find("?")+1:]

    values = {}

    for keyval in vars.split("&"):
        (key, value) = keyval.split("=")
        values[key] = value

    print values

    return values

K_BS = 0
K_CAPS = 1
K_NUM = 2
K_SPACE = 3

class KeyBoardButton(wxButton):
    def __init__(self, parent, modes):
        wxButton.__init__(self, 
                          parent, 
                          ID_KEYBOARD, 
                          modes[0],
                          size=wxSize(60,60))

        self.modes = modes

        self.SetBackgroundColour('#0000FF')
        self.SetForegroundColour('WHITE')

    def isSpecial(self):
        return False

    def setMode(self, mode):
        self.SetLabel(self.modes[mode])


class KeyBoardSpecialButton(wxButton):
    def __init__(self, parent, special, text):
        wxButton.__init__(self, 
                          parent, 
                          ID_KEYBOARD, 
                          text,
                          size=wxSize(60,60))

        self.special = special

        self.SetBackgroundColour('#0000AA')
        self.SetForegroundColour('WHITE')

    def isSpecial(self):
        return True

    def getSpecial(self):
        return self.special

    def setMode(self, mode):
        pass


class SodaKeyBoard(wxPanel):
    def __init__(self, parent, ID, pos, size, target):
        wxPanel.__init__(self, parent, ID, pos, size)

        font = self.GetFont()
        font.SetPointSize(30)
        self.SetFont(font)

        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetForegroundColour(parent.GetForegroundColour())


        self.buttons = []
        self.mode = 0
        # 0x1 = Caps
        # 0x2 = Num
        # 0x3 = both

        # qwertyuiop
        # asdfghjkl <-
        # caps 123 zxcvbvm space

        # 1234567890
        # `   -=[]\
        #    ,./;'
        # !@#$%^&*[]
        # ~   _+{}|
        #    <>?:"

        alphaKeys = [['q','w','e','r','t','y','u','i','o','p'],
                     ['a','s','d','f','g','h','j','k','l', K_BS],
                     [K_CAPS, K_NUM, 'z','x','c','v','b','n','m', K_SPACE]]
        AlphaKeys = [['Q','W','E','R','T','Y','U','I','O','P'],
                     ['A','S','D','F','G','H','J','K','L', K_BS],
                     [K_CAPS, K_NUM, 'Z','X','C','V','B','N','M', K_SPACE]]
        numKeys   = [['1','2','3','4','5','6','7','8','9','0'],
                     ['`', '', '', '','-','=','[',']','\\', K_BS],
                     [K_CAPS, K_NUM,  '',',','.','/',';','\'','', K_SPACE]]
        NumKeys   = [['!','@','#','$','%','^','&&','*','[',']'],
                     ['~', '', '', '','_','+','{','}','|', K_BS],
                     [K_CAPS, K_NUM,  '','<','>','?',':','"','', K_SPACE]]

        sizer = wxGridSizer(len(alphaKeys), len(alphaKeys[0]), 3, 3)

        self.SetSizer(sizer)

        for row in range(0, len(alphaKeys)):
            for col in range(0, len(alphaKeys[row])):

                code = alphaKeys[row][col]

                button = None

                if code == K_BS:
                    button = KeyBoardSpecialButton(self, K_BS, "<-")
                elif code == K_CAPS:
                    button = KeyBoardSpecialButton(self, K_CAPS, "cap")
                elif code == K_NUM:
                    button = KeyBoardSpecialButton(self, K_NUM, "num")
                elif code == K_SPACE:
                    button = KeyBoardSpecialButton(self, K_SPACE, "SPCE")
                else:
                    values = [ alphaKeys[row][col],
                               AlphaKeys[row][col],
                               numKeys[row][col],
                               NumKeys[row][col] ]

                    button = KeyBoardButton(self, values)

                sizer.Add(button)
                self.buttons.append(button)
                button.Bind(EVT_LEFT_DOWN, self.on_keypress)
                button.Bind(EVT_LEFT_DCLICK, self.on_double_keypress)

        self.target = target

    def updateMode(self, mode):
        self.mode = mode
        for b in self.buttons:
            b.setMode(self.mode)

    def on_double_keypress(self, event):
        # Do it twice, pesky double click detection
        self.on_keypress(event)
        self.on_keypress(event)

    def on_keypress(self, event):
        button = event.GetEventObject()
        if button.isSpecial():
            code = button.getSpecial()
            if code == K_BS:
                self.target.Remove(
                                   self.target.GetLineLength(0) - 1, 
                                   self.target.GetLineLength(0)
                                  )
            elif code == K_CAPS:
                self.updateMode(self.mode ^ 0x1)

            elif code == K_NUM:
                self.updateMode(self.mode ^ 0x2)

            elif code == K_SPACE:
                self.target.WriteText(" ")

            else:
                print "Unrecognized Code"

        else:
            self.target.WriteText(button.GetLabel())


class SodaButton(wxButton):
    def __init__(self, parent, ID, Text):
        wxButton.__init__(self, parent, ID, Text,
                size=wxSize(SodaPanel.leftBarWidth, -1))

        # Hackomatic
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetForegroundColour(parent.GetForegroundColour())

        font = self.GetFont()
        font.SetPointSize(50)
        self.SetFont(font)

class SodaPanel(wxPanel):
    leftBarWidth = 150
    topBarHeight = 50
    leftBarColour = 'ORANGE'

    def __init__(self, parent, ID, pos, size):
        wxPanel.__init__(self, parent, ID, pos, size)

        # Hackomatic
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetForegroundColour(parent.GetForegroundColour())

        # Build Generic Setup
        self.VertSizer = wxBoxSizer(wxVERTICAL)

        # Top Padding
        self.TopSpaceSizer = wxBoxSizer(wxHORIZONTAL)

        self.TopSpaceSizer.AddSpacer(wxSize(self.leftBarWidth,
                                            self.topBarHeight))

        self.StatusLabel = wxStaticText(self, -1, "Status: ",
                                        size = wxSize(-1, self.topBarHeight),
                                        style = wxALIGN_LEFT)

        self.TopSpaceSizer.Add(self.StatusLabel, 0)

        self.StatusTextLabel = wxStaticText(self, -1, "Idle")

        self.TopSpaceSizer.Add(self.StatusTextLabel, 1)



        self.VertSizer.Add(self.TopSpaceSizer)

        self.MainSizer = wxBoxSizer(wxHORIZONTAL)

        self.LeftBarSizer = wxBoxSizer(wxVERTICAL)

        leftBarTopSpacer = wxStaticText(self, 
                                  -1, 
                                  "",
                                  wxDefaultPosition, 
                                  wxSize(self.leftBarWidth,25))
        self.LeftBarSizer.Add(leftBarTopSpacer)

        self.ContentSizer = wxBoxSizer(wxVERTICAL)

        self.MainSizer.Add(self.LeftBarSizer)
        self.MainSizer.Add(self.ContentSizer)

        self.VertSizer.Add(self.MainSizer)

        self.SetSizer(self.VertSizer)

    def AddLeftButton(self, Widget):
        """
        Wraps all the parameters for adding a button to the left bar.
        """

        self.LeftBarSizer.Add(
                    Widget,
                    1, # re-proportion
                    wxALIGN_CENTER_HORIZONTAL
                    )

        # leftBarSpacer = wxPanel(self, 
        #                           -1, 
        #                           wxDefaultPosition, 
        #                           wxSize(self.leftBarWidth,25))

        # leftBarSpacer.SetOwnBackgroundColour(self.leftBarColour)
        # self.LeftBarSizer.Add(leftBarSpacer, 1, wxALIGN_CENTER)

    def SetStatusText(self, text, colour='WHITE'):
        self.StatusTextLabel.SetLabel(text)
        self.StatusTextLabel.SetForegroundColour(colour)


class SodaPurchasePanel(SodaPanel):
    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.AddLeftButton(
                SodaButton(
                    self,
                    ID_LOGOUT, 
                    'Logout'
                    )
                                   )

        self.UserLabel = wxStaticText(
                self,
                -1,
                "UserLabel"
                )
        self.BalanceLabel = wxStaticText(
                self,
                -1,
                "BalanceLabel"
                )
        self.TimerLabel = wxStaticText(
                self,
                -1,
                "TimerLabel"
                )

        self.ContentSizer.Add(self.UserLabel)
        self.ContentSizer.Add(self.BalanceLabel)
        self.ContentSizer.Add(self.TimerLabel)

        self.purchaseLog = wxStaticText(
                                        self,
                                        -1,
                                        "",
                                        wxDefaultPosition,
                                        wxSize(400, -1)
                                        )

        self.ContentSizer.Add(self.purchaseLog)

    def SetUser(self, user):
        self.UserLabel.SetLabel("User: " + user)

    def SetBalance(self, balance):
        self.BalanceLabel.SetLabel("Balance: " + str(balance))

    def SetTTL(self, ttl):
        self.TimerLabel.SetLabel("Timeout in " + str(ttl) + " seconds")

    def AddLog(self, message):
        self.purchaseLog.SetLabel(self.purchaseLog.GetLabel() + "\n" + message)

    def Clear(self):
        self.UserLabel.SetLabel("")
        self.BalanceLabel.SetLabel("")
        self.TimerLabel.SetLabel("")
        self.purchaseLog.SetLabel("")


class SodaFrame(wxFrame):
    '''The Main Window of the soda UI

    The GUI section is implemented as a series of panels that are
    constructed via the make*() functions.  They are hidden/revealed by
    the begin*/end* functions that are in turn invoked by the
    changeState function.

    Changes in state can be triggered by interactions with the servio
    interface, or via the buttons contained within the panels.  The
    servio interface callbacks are the handle* functions.  The button
    callbacks are on* and the event callbacks (generated by the button
    handlers and the handle*) are on*Event.  We can change naming
    schemes later if we feel so inclined.

    We currently have the following states:

    Login Idle - In the old version, this shows stats of soda purchases.
                 For us, it could show other things, perhaps rotating 
                 occasionally.
    Login - Interaction with the screen keyboard to login and password,
            etc.

    Purchase - This is essentially the logged-in screen.  I didn't want
               all of the states to be log*.  This state runs a timer
               that counts to zero.  This replaces tha javascript update
               hack of the old system.  It currently tries to trigger a
               logout at the end, but the backend currently executes a
               logout, so this doesn't really need to happen.

    The ServIO callback handlers are executed from a separate thread,
    so you need to be careful when calling thread-unsafe gui functions.
    Most of the interactions I have programmed come through
    wx.PostEvent, which is threadsafe.
    '''

    state = STATE_LOGIN_IDLE

    backgroundColour = 'BLACK'
    foregroundColour = 'WHITE'

    passwordLimit = 3


    def __init__(self, parent, ID, title, bus):
        '''
        Initializes the Frame with the title, builds the panels, and
        starts the system in the LoginIdle State
        '''
        wxFrame.__init__(self, parent, ID, title,
                         wxDefaultPosition, wxSize(800, 600))

        self.SetBackgroundColour(self.backgroundColour)
        self.SetForegroundColour(self.foregroundColour)

        self.font = wxFont(30, 
                      wxFONTFAMILY_DEFAULT,
                      wxFONTSTYLE_NORMAL,
                      wxFONTWEIGHT_NORMAL,
                      False,
                      "lcars"
                      )

        self.SetFont(self.font)

        self.makeLoginIdlePanel()
        self.makeLoginPanel()
        self.makePasswordPanel()
        self.makePurchasePanel()

        self.Bind(EVT_LOGIN_EVENT, self.onLoginEvent)
        self.Bind(EVT_PASSWORD_EVENT, self.onPasswordEvent)
        self.Bind(EVT_LOGOUT_EVENT, self.onLogoutEvent)
        self.Bind(EVT_BOUGHT_EVENT, self.onBoughtEvent)
        self.Bind(EVT_TTL_EVENT, self.onTtlEvent)
        self.Bind(EVT_BALANCE_EVENT, self.onBalanceEvent)

        self.beginLoginIdle()

        self.bus = bus

    def changeState(self, new_state):
        '''
        Close down the old state and enter new_state, if it
        differs.
        '''
        if self.state == new_state:
            return

        if self.state == STATE_LOGIN_IDLE:
            self.endLoginIdle()
        elif self.state == STATE_LOGIN:
            self.endLogin()
        elif self.state == STATE_PASSWORD:
            self.endPassword()
        elif self.state == STATE_PURCHASE:
            self.endPurchase()
        else:
            print "Unknown Old State"

        if new_state == STATE_LOGIN_IDLE:
            self.beginLoginIdle()
        elif new_state == STATE_LOGIN:
            self.beginLogin()
        elif new_state == STATE_PASSWORD:
            self.beginPassword()
        elif new_state == STATE_PURCHASE:
            self.beginPurchase()
        else:
            print "Unknown State"

        self.state = new_state

    #
    # Functions associated with the LoginIdle State
    #
    def makeLoginIdlePanel(self):
        self.idlePanel = SodaPanel(self, -1, wxPoint(0,0), self.GetSize())

        self.idlePanelSizer = wxBoxSizer(wxVERTICAL)

        loginButton = SodaButton(self.idlePanel, ID_LOGIN, 'Login')

        self.idlePanel.AddLeftButton(loginButton)

        self.Bind(EVT_BUTTON, self.onLogin, id=ID_LOGIN)

        self.idlePanel.SetStatusText("Idle")

        self.idlePanel.Layout()
        self.idlePanel.Show(false)

    def beginLoginIdle(self):
        self.idlePanel.Show(true);
        print "beginLoginIdle"

    def endLoginIdle(self):
        self.idlePanel.Show(false);
        print "endLoginIdle"

    def onLogin(self, event):
        self.changeState(STATE_LOGIN)

    # 
    # Functions associated with the Login State
    #
    def makeLoginPanel(self):
        self.loginPanel = SodaPanel(self, -1, wxPoint(0,0), self.GetSize())


        self.loginPanel.AddLeftButton(SodaButton(self.loginPanel, 
                                                  ID_DOLOGIN, 
                                                  'Login'))

        self.loginPanel.AddLeftButton(SodaButton(self.loginPanel,
                                                 ID_CANCEL,
                                                 'Cancel'))

        self.Bind(EVT_BUTTON, self.onDoLogin, id=ID_DOLOGIN)
        self.Bind(EVT_BUTTON, self.onLoginCancel, id=ID_CANCEL)

        loginInfoSizer = wxBoxSizer(wxHORIZONTAL)

        loginLabel = wxStaticText(
                self.loginPanel,
                -1,
                "Login: ",
                style = wxALIGN_RIGHT
                )

        loginInfoSizer.Add(loginLabel, 1, wxALIGN_CENTER)

        self.loginInput = wxTextCtrl(
                self.loginPanel, 
                -1,
                "",
                wxDefaultPosition,
                wxSize(200, -1) # XXX
                )

        loginInfoSizer.Add(self.loginInput, 1, wxALIGN_CENTER)

        self.loginPanel.ContentSizer.Add(loginInfoSizer)

        self.loginPanel.ContentSizer.AddSpacer(wxSize(50,50))
        self.loginPanel.ContentSizer.Add(SodaKeyBoard(self.loginPanel,
            -1, wxDefaultPosition, wxSize(400, 400), self.loginInput))

        self.loginPanel.SetStatusText('Authenticating', 'YELLOW')

        self.loginPanel.Layout()
        self.loginPanel.Show(false)

    def beginLogin(self):
        self.loginPanel.Show(true)
        print "beginLogin"

    def endLogin(self):
        self.loginInput.Clear()
        self.loginPanel.Show(false)
        print "endLogin"

    def onDoLogin(self, event):
        login = self.loginInput.GetLineText(0)
        self.loginInput.Clear()

        if len(login) > 0:
            self.querytag = servio.genTag()
            self.bus.send(["LOGIN",
                           login])

    def onLoginCancel(self, event):
        # Inputs are cleared by the end* functions.
        self.changeState(STATE_LOGIN_IDLE)

    def onLoginEvent(self, event):
        print "Login Event"

        self.user = event.user
        self.balance = event.balance
        self.timeout = int(event.timeout)
        self.changeState(STATE_PURCHASE)

    def onPasswordEvent(self, event):
        print "Password Event"
        self.user = event.user
        self.balance = event.balance
        self.timeout = int(event.ttl)
        self.hash = event.hash
        self.changeState(STATE_PASSWORD)

    # 
    # Functions associated with the Password State
    #
    def makePasswordPanel(self):
        self.passwordPanel = SodaPanel(self, -1, wxPoint(0,0), self.GetSize())

        self.passwordPanel.AddLeftButton(SodaButton(self.passwordPanel, 
                                                  ID_DOPASSWORD, 
                                                  'Login'))

        self.passwordPanel.AddLeftButton(SodaButton(self.passwordPanel,
                                                 ID_CANCEL,
                                                 'Cancel'))

        self.Bind(EVT_BUTTON, self.onDoPassword, id=ID_DOPASSWORD)

        passwordInfoSizer = wxBoxSizer(wxHORIZONTAL)

        self.passwordLabel = wxStaticText(
                self.passwordPanel,
                -1,
                "Password:",
                style=wxALIGN_RIGHT
                )

        passwordInfoSizer.Add(self.passwordLabel, 1, wxALIGN_CENTER)

        self.passwordInput = wxTextCtrl(
                self.passwordPanel, 
                -1,
                "",
                wxDefaultPosition,
                wxSize(200, -1), # XXX
                wxPASSWORD
                )

        passwordInfoSizer.Add(self.passwordInput, 1, wxALIGN_CENTER)

        self.passwordPanel.ContentSizer.Add(passwordInfoSizer)
        self.passwordPanel.ContentSizer.AddSpacer(wxSize(50,50))
        self.passwordPanel.ContentSizer.Add(SodaKeyBoard(self.passwordPanel,
            -1, wxDefaultPosition, wxSize(400, 400), self.passwordInput))

        self.passwordPanel.Layout()
        self.passwordPanel.Show(false)

    def beginPassword(self):
        self.passwordPanel.SetStatusText('Authenticating ' + self.user, 'YELLOW')
        self.passwordPanel.Show(true)
        self.passwordCount = self.passwordLimit
        print "beginPassword"

    def endPassword(self):
        self.passwordInput.Clear()
        self.passwordPanel.Show(false)
        print "endPassword"

    def onDoPassword(self, event):
        password = self.passwordInput.GetLineText(0)
        self.passwordInput.Clear()

        if self.hash is not None:
            if crypt.crypt(password, self.hash) == self.hash:
                self.bus.send(["LOGIN", self.user, self.balance])
                return
    
        self.passwordCount = self.passwordCount - 1

        if self.passwordCount == 0:
            self.bus.send(["LOGIN-DENIED", self.user])
            self.changeState(STATE_LOGIN_IDLE)

    #
    # Functions associated with the Purchase State
    #
    def makePurchasePanel(self):
        self.purchasePanel = SodaPurchasePanel(self, 
                                               -1, 
                                               wxPoint(0,0), 
                                               self.GetSize())

        self.purchasePanel.Bind(EVT_BUTTON, self.onLogout, id=ID_LOGOUT)

        self.purchasePanel.Layout()
        self.purchasePanel.Show(false)

        self.purchaseTimer = wxTimer(self, 0)
        self.Bind(EVT_TIMER, self.onPurchaseTimerFire)

        self.purchaseTimer.Stop()

    def beginPurchase(self):
        self.purchasePanel.SetStatusText('Ready for ' + self.user, 'GREEN')
        self.purchasePanel.SetUser(self.user)
        self.purchasePanel.SetBalance(self.balance)
        # These vars should be setup by the onLoginEvent
        self.updatePurchaseTimerLabel()

        # Kick off the timer.
        self.purchaseTimer.Start(1000)

        self.purchasePanel.Show(true)
        print "beginPurchase"

    def endPurchase(self):
        self.purchasePanel.Clear()
        print "endPurchase"

    def onLogout(self, event):
        evt = LogoutEvent()
        wx.PostEvent(self, evt)

    def onLogoutEvent(self, event):
        self.bus.send(["LOGOUT"])
        self.changeState(STATE_LOGIN_IDLE)

    def onBoughtEvent(self, event):
        self.balance = event.balance
        self.timeout = int(event.ttl)

        self.purchasePanel.SetBalance(self.balance)
        self.purchasePanel.AddLog(event.item + " for " + event.price)

        print "Bought Event: " + event.item

    def onTtlEvent(self, event):
        self.timeout = int(event.timeout)
        print "Ttl Event"

    def onBalanceEvent(self, event):
        self.balance = int(event.balance)
        self.purchasePanel.SetBalance(self.balance)
        print "Balance Event"

    # Gui helper
    def updatePurchaseTimerLabel(self):
        self.purchasePanel.SetTTL(str(self.timeout))

    def onPurchaseTimerFire(self, event):
        self.timeout = max(self.timeout - 1, 0)
        #if self.timeout <=  0:
        #    evt = LogoutEvent()
        #    wx.PostEvent(self, evt)

        self.updatePurchaseTimerLabel()

    #
    # ServIO callback handlers.
    #

    def handleIndexPhp(self, msg, values):
        '''
        Reverse engineer the old display style
        '''
        if msg == "LOGGEDIN":
            evt = LoginEvent(user=values["login"],
                             balance=values["balance"],
                             timeout=values["TTL"])
            wx.PostEvent(self, evt)

        elif msg == "LOGGEDOUT" or msg == "AUTOLOGGEDOUT" or msg == "TIMEOUT" or msg == "LOGOUT":
            evt = LogoutEvent()
            wx.PostEvent(self, evt)

        elif msg == "BOUGHT":
            evt = BoughtEvent(user=values["login"],
                              balance=values["balance"],
                              timeout=values["TTL"],
                              item=values["item"])
            wx.PostEvent(self, evt)

        elif msg == "PASSWORD":
            evt = PasswordEvent(user=values["login"],
                                balance=values["balance"],
                                hash=values["hash"],
                                ttl=values["TTL"])
            wx.PostEvent(self, evt)

        else:
            print "unknown msg: " + msg



    def handleUiOpen(self, data):
        values = urldecode(data[1])

        if 'msg' in values:
            self.handleIndexPhp(values['msg'], values)
        elif 'message' in values:
            self.handleIndexPhp(values['message'], values)
        else:
            print "msg not present in UI-OPEN"
            return

    def handleSysSet(self, data):
        if data[1] == "MOZ-KIOSK":
            if data[2] == "real_location":
                self.handleUiOpen(["UI-OPEN",data[4]])

    def handleUiLoggedIn(self, data):
        evt = LoginEvent(user=data[1],
                balance=data[2],
                timeout=data[3],
                anonymous=data[4])
        wx.PostEvent(self, evt)

    def handleUiLoggedOut(self, data):
        evt = LogoutEvent()
        wx.PostEvent(self, evt)

    def handleUiPassword(self, data):
        evt = PasswordEvent(user=data[1],
                            balance=data[2],
                            hash=data[3],
                            ttl=data[4])
        wx.PostEvent(self, evt)

    def handleUiBought(self,data):
        evt = BoughtEvent(item=data[1],
                price=data[2],
                balance=data[3],
                ttl=data[4])
        wx.PostEvent(self, evt)

    def handleUiBalance(self,data):
        evt = BalanceEvent(balance=data[1])
        wx.PostEvent(self, evt)

    def handleUiTtl(self,data):
        evt = TtlEvent(ttl=data[1])
        wx.PostEvent(self, evt)

class SodaApp(wxApp):
    def OnInit(self):
        self.bus = servio.ServIO("PySodaGui", "0.0")
        self.bus.defaultHandler(servio.noop_handler)

        frame = SodaFrame(NULL, -1, "Hello World", self.bus)
        frame.Show(true)
        self.SetTopWindow(frame)

        #self.bus.watchMessage("UI-OPEN", frame.handleUiOpen)
        #self.bus.watchMessage("MOZ-OPEN", frame.handleUiOpen)
        #self.bus.watchMessage("SYS-SET", frame.handleSysSet)

        self.bus.watchMessage("UI-LOGGEDIN", frame.handleUiLoggedIn)
        self.bus.watchMessage("UI-LOGGEDOUT", frame.handleUiLoggedOut)
        self.bus.watchMessage("UI-PASSWORD", frame.handleUiPassword)
        self.bus.watchMessage("UI-BOUGHT", frame.handleUiBought)
        self.bus.watchMessage("UI-BALANCE", frame.handleUiBalance)
        self.bus.watchMessage("UI-TTL", frame.handleUiTtl)

        self.bus_thread = threading.Thread(target=self.bus.receive)
        self.bus_thread.start()

        return true

    def Exit(self):
        self.bus.exit()

app = SodaApp(0)
app.MainLoop()
app.Exit()
