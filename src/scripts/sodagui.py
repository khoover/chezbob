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
# + I don't think I am using this...
# UI-FP-NOTICE | count | message | complete [01]

# Purple #946ee1
SodaPurple = '#946ee1'
# Orange #ff9e00
SodaOrange = '#ff9e00'
SodaDarkOrange = '#ff9e00'
# Red    #c64549
SodaRed    = '#c64549'

SodaLightGreen = '#aaffaa'

SodaButtonColor = SodaPurple
SodaButtonTextColor = '#000000'

SodaKeyBoardFontSize = 30
SodaStatsFontSize = 30
SodaLargeSize = 50

from wxPython.wx import *
import servio
import threading
import wx.lib.newevent
import crypt
import PHPUnserialize

sodaBgImage = wxImage("sodagui-bg.png")
sodaBgImageBitmap = None

# Button identifiers
ID_LOGOUT  = 102
ID_LOGIN   = 103
ID_DOLOGIN = 104
ID_DOPASSWORD = 105
ID_KEYBOARD   = 106
ID_CANCEL     = 107
ID_FPLEARN    = 108

STATE_LOGIN_IDLE = 1
STATE_LOGIN      = 2
STATE_PASSWORD   = 3
STATE_PURCHASE   = 4
STATE_FPLEARN    = 5

LogoutEvent, EVT_LOGOUT_EVENT = wx.lib.newevent.NewEvent()
LoginEvent, EVT_LOGIN_EVENT = wx.lib.newevent.NewEvent()
PasswordEvent, EVT_PASSWORD_EVENT = wx.lib.newevent.NewEvent()
BoughtEvent, EVT_BOUGHT_EVENT = wx.lib.newevent.NewEvent()
TtlEvent, EVT_TTL_EVENT = wx.lib.newevent.NewEvent()
BalanceEvent, EVT_BALANCE_EVENT = wx.lib.newevent.NewEvent()
FpEvent, EVT_FP_EVENT = wx.lib.newevent.NewEvent()

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

def monetize(val):
    return "$%0.2f" % (int(val) / 100.0)

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
        font.SetPointSize(SodaKeyBoardFontSize)
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
        self.SetBackgroundColour(SodaButtonColor)
        self.SetForegroundColour(SodaButtonTextColor)

        font = self.GetFont()
        font.SetPointSize(45)
        self.SetFont(font)

class SodaIdleStatsPanel(wxPanel):
    def __init__(self, parent, ID, pos, size):
        wxPanel.__init__(self, parent, ID, pos, size)

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


class SodaPanel(wxPanel):
    leftBarWidth = 150
    topBarHeight = 40
    topLineHeight = 40
    botLineHeight = 40
    buttonSpacing = 2
    leftBarColour = 'ORANGE'

    def __init__(self, parent, ID, pos, size):
        wxPanel.__init__(self, parent, ID, pos, size)

        # Hackomatic
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetForegroundColour(parent.GetForegroundColour())

        global sodaBgImageBitmap
        if sodaBgImageBitmap is None:
            sodaBgImageBitmap = sodaBgImage.ConvertToBitmap()

        wxStaticBitmap(self, -1, sodaBgImageBitmap)

        # Build Generic Setup
        self.VertSizer = wxBoxSizer(wxVERTICAL)

        # Top Padding
        self.TopSpaceSizer = wxBoxSizer(wxHORIZONTAL)

        self.TopSpaceSizer.AddSpacer(wxSize(self.leftBarWidth,
                                            self.topBarHeight))

        self.TopSpaceSizer.AddSpacer(wxSize(30, -1)) # Move past the curve

        self.StatusLabel = wxStaticText(self, -1, "Status: ",
                                        size = wxSize(-1, self.topBarHeight),
                                        style = wxALIGN_LEFT)

        self.TopSpaceSizer.Add(self.StatusLabel, 0)

        self.StatusTextLabel = wxStaticText(self, -1, "Idle")


        self.TopSpaceSizer.Add(self.StatusTextLabel, 1)

        self.VertSizer.Add(self.TopSpaceSizer)

        self.VertSizer.AddSpacer(wxSize(-1, self.topLineHeight))

        self.MainSizer = wxBoxSizer(wxHORIZONTAL)

        self.LeftBarSizer = wxBoxSizer(wxVERTICAL)

        leftBarTopSpacer = wxStaticText(self, 
                                  -1, 
                                  "",
                                  wxDefaultPosition, 
                                  wxSize(self.leftBarWidth,25))
        self.LeftBarSizer.Add(leftBarTopSpacer)

        buttonTopSpacer = wxPanel(self, -1, 
                        size=wxSize(self.leftBarWidth,
                        self.buttonSpacing))
        buttonTopSpacer.SetBackgroundColour('BLACK')
        self.LeftBarSizer.Add(buttonTopSpacer)

        self.ContentSizer = wxBoxSizer(wxVERTICAL)
        self.ResetContentSizer()


        self.MainSizer.Add(self.LeftBarSizer)
        self.MainSizer.Add(self.ContentSizer)

        self.VertSizer.Add(self.MainSizer)

        self.SetSizer(self.VertSizer)

    def ResetContentSizer(self):
        self.ContentSizer.Clear()

        # Force the content sizer as wide as the area.
        self.ContentSizer.AddSpacer(
                wxSize(self.GetContentWidth(), 0))

    def GetContentWidth(self):
        return self.GetSize().GetWidth() - self.leftBarWidth


    def AddLeftButton(self, Widget):
        """
        Wraps all the parameters for adding a button to the left bar.
        """

        self.LeftBarSizer.Add(
                    Widget,
                    1, # re-proportion
                    wxALIGN_CENTER_HORIZONTAL
                    )

        buttonSpacer = wxPanel(self, -1, 
                        size=wxSize(self.leftBarWidth,
                        self.buttonSpacing))
        buttonSpacer.SetBackgroundColour('BLACK')

        self.LeftBarSizer.Add(buttonSpacer)

    def AddLeftSpacer(self, size):
        self.LeftBarSizer.AddSpacer(size)

    def SetStatusText(self, text, colour='WHITE'):
        self.StatusTextLabel.SetLabel(text)
        self.StatusTextLabel.SetForegroundColour(colour)

class SodaLoginIdlePanel(SodaPanel):

    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.idlePanelSizer = wxBoxSizer(wxVERTICAL)

        loginButton = SodaButton(self, ID_LOGIN, 'LOGIN')

        self.AddLeftButton(loginButton)

        self.SetStatusText("Idle")

        self.statsPanel = None


    def MakeSodaStatsPanel(self):
        if self.statsPanel is not None:
            self.statsPanel.Destroy()

        self.statsPanel = SodaIdleSodaStatsPanel(self, -1,
                wxDefaultPosition, wxSize(self.GetContentWidth(), -1))

        self.ResetContentSizer()
        self.ContentSizer.Add(self.statsPanel)


        self.ContentSizer.Layout()


class SodaLoginPanel(SodaPanel):
    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.AddLeftButton(SodaButton(self,
            ID_DOLOGIN, 
            'LOGIN'))

        self.AddLeftButton(SodaButton(self,
            ID_CANCEL,
            'CANCEL'))

        loginInfoSizer = wxBoxSizer(wxHORIZONTAL)

        loginLabel = wxStaticText(
                self,
                -1,
                "Login: ",
                style = wxALIGN_RIGHT
                )

        loginInfoSizer.Add(loginLabel, 1, wxALIGN_CENTER)

        self.loginInput = wxTextCtrl(
                self, 
                -1,
                "",
                wxDefaultPosition,
                wxSize(200, -1) # XXX
                )

        loginInfoSizer.Add(self.loginInput, 1, wxALIGN_CENTER)

        self.ContentSizer.Add(loginInfoSizer)

        self.ContentSizer.AddSpacer(wxSize(50,50))
        self.ContentSizer.Add(SodaKeyBoard(self,
            -1, wxDefaultPosition, wxSize(400, 400), self.loginInput),
            flag=wxALIGN_CENTER, proportion=1)

        self.SetStatusText('Authenticating', 'YELLOW')

    def GetLogin(self):
        return self.loginInput.GetLineText(0)

    def Clear(self):
        self.loginInput.Clear()


class SodaPasswordPanel(SodaPanel):
    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)


        self.AddLeftButton(SodaButton(self, 
            ID_DOPASSWORD, 
            'Login'))

        self.AddLeftButton(SodaButton(self,
            ID_CANCEL,
            'Cancel'))


        passwordInfoSizer = wxBoxSizer(wxHORIZONTAL)

        self.passwordLabel = wxStaticText(
                self,
                -1,
                "Password:",
                style=wxALIGN_RIGHT
                )

        passwordInfoSizer.Add(self.passwordLabel, 1, wxALIGN_CENTER)

        self.passwordInput = wxTextCtrl(
                self, 
                -1,
                "",
                wxDefaultPosition,
                wxSize(200, -1), # XXX
                wxPASSWORD
                )

        passwordInfoSizer.Add(self.passwordInput, 1, wxALIGN_CENTER)

        self.ContentSizer.Add(passwordInfoSizer)
        self.ContentSizer.AddSpacer(wxSize(50,50))
        self.ContentSizer.Add(SodaKeyBoard(self,
            -1, wxDefaultPosition, wxSize(400, 400), self.passwordInput))

    def GetPassword(self):
        return self.passwordInput.GetLineText(0)

    def Clear(self):
        self.passwordInput.Clear()

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

        self.AddLeftSpacer(wxSize(-1, 240))

        self.AddLeftButton(
                SodaButton(
                    self,
                    ID_FPLEARN,
                    'Learn FP'
                    )
                   )

        self.UserSalutations = wxStaticText(
                self,
                -1,
                "Hello "
                )
        self.UserLabel = wxStaticText(
                self,
                -1,
                "UserLabel",
                style=wxALIGN_LEFT
                )
        self.UserLabel.SetForegroundColour(SodaDarkOrange)

        self.UserLabelComma = wxStaticText(
                self,
                -1,
                ","
                )

        self.UserSizer = wxBoxSizer(wxHORIZONTAL)

        self.UserSizer.Add(self.UserSalutations)
        self.UserSizer.Add(self.UserLabel)
        self.UserSizer.Add(self.UserLabelComma)


        self.BalanceText = wxStaticText(
                self,
                -1,
                "You have a Balance of "
                )
        self.BalanceLabel = wxStaticText(
                self,
                -1,
                "BalanceLabel"
                )

        self.BalanceSizer = wxBoxSizer(wxHORIZONTAL)
        self.BalanceSizer.Add(self.BalanceText)
        self.BalanceSizer.Add(self.BalanceLabel)

        self.TimerLabel = wxStaticText(
                self,
                -1,
                "TimerLabel"
                )



        self.ContentSizer.Add(self.UserSizer)
        self.ContentSizer.Add(self.BalanceSizer)
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
        self.UserLabel.SetLabel(user)
        self.UserSizer.Layout()

    def SetBalance(self, balance):
        self.BalanceLabel.SetLabel(str(monetize(balance)))

    def SetTTL(self, ttl):
        self.TimerLabel.SetLabel("Timeout in " + str(ttl) + " seconds")

    def AddLog(self, message):
        self.purchaseLog.SetLabel(self.purchaseLog.GetLabel() + "\n" + message)

    def Clear(self):
        self.UserLabel.SetLabel("")
        self.BalanceLabel.SetLabel("")
        self.TimerLabel.SetLabel("")
        self.purchaseLog.SetLabel("")

class SodaFPPanel(SodaPanel):
    def __init__(self, parent, ID, pos, size):
        SodaPanel.__init__(self, parent, ID, pos, size)

        self.AddLeftButton(
                SodaButton(
                    self,
                    ID_CANCEL, 
                    'CANCEL'
                    )
                         )

        self.StatusLabel = wxStaticText(
                self,
                -1,
                ""
                )
        self.Instructions = wxStaticText(
                self,
                -1,
                "PLEASE TRAIN YOUR\nFINGERPRINT ON THE\nREADER BELOW...",
                style=wxALIGN_CENTER
                )
        self.Instructions.SetForegroundColour(SodaOrange)

        instrfont = self.Instructions.GetFont()
        instrfont.SetPointSize(40)
        self.Instructions.SetFont(instrfont)


        self.UpperSizer = wxBoxSizer(wxHORIZONTAL)
        self.UpperLeftSizer = wxBoxSizer(wxVERTICAL)

        self.UpperLeftSizer.Add(self.StatusLabel)
        self.UpperLeftSizer.Add(self.Instructions)

        self.UpperSizer.Add(self.UpperLeftSizer, proportion=1)
        self.UpperSizer.AddSpacer(wxSize(300,-1))

        self.CountPrompt = wxStaticText(
                self,
                -1,
                "Please enter your fingerprint "
                )
        self.CountNumber = wxStaticText(
                self,
                -1,
                "3"
                )
        self.CountPostPrompt = wxStaticText(
                self,
                -1,
                " more time(s)"
                )

        self.CountSizer = wxBoxSizer(wxHORIZONTAL)
        self.CountSizer.Add(self.CountPrompt)
        self.CountSizer.Add(self.CountNumber)
        self.CountSizer.Add(self.CountPostPrompt)

        self.TimerLabel = wxStaticText(
                self,
                -1,
                "TimerLabel"
                )

        self.ContentSizer.Add(self.UpperSizer)
        self.ContentSizer.Add(self.CountSizer)
        self.ContentSizer.Add(self.TimerLabel)

        self.UpperSizer.Layout()


    def SetCount(self, count):
        self.CountNumber.SetLabel(str(count))
        self.CountSizer.Layout()

    def SetMessage(self, message):
        self.StatusLabel.SetLabel(message)
        self.UpperSizer.Layout()

    def SetTTL(self, ttl):
        self.TimerLabel.SetLabel("Timeout in " + str(ttl) + " seconds")

    def Clear(self):
        self.StatusLabel.SetLabel("")
        self.TimerLabel.SetLabel("")



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
        self.makeFpPanel()

        self.Bind(EVT_LOGIN_EVENT, self.onLoginEvent)
        self.Bind(EVT_PASSWORD_EVENT, self.onPasswordEvent)
        self.Bind(EVT_LOGOUT_EVENT, self.onLogoutEvent)
        self.Bind(EVT_BOUGHT_EVENT, self.onBoughtEvent)
        self.Bind(EVT_TTL_EVENT, self.onTtlEvent)
        self.Bind(EVT_BALANCE_EVENT, self.onBalanceEvent)
        self.Bind(EVT_FP_EVENT, self.onFpEvent)

        self.beginLoginIdle()

        self.TTLTimer = wxTimer(self, 0)
        self.Bind(EVT_TIMER, self.onTTLTimerFire)

        self.TTLTimer.Stop()

        self.bus = bus

        self.FPServVL = self.bus.getVarList("FPSERV")

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
        elif self.state == STATE_FPLEARN:
            self.endFpLearn()
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
        elif new_state == STATE_FPLEARN:
            self.beginFpLearn()
        else:
            print "Unknown State"

        self.state = new_state

    #
    # Functions associated with the LoginIdle State
    #
    def makeLoginIdlePanel(self):
        self.idlePanel = SodaLoginIdlePanel(self, 
                                            -1, 
                                            wxPoint(0,0), 
                                            self.GetSize())

        self.Bind(EVT_BUTTON, self.onLogin, id=ID_LOGIN)

        self.idlePanel.Layout()
        self.idlePanel.Show(false)

    def beginLoginIdle(self):
        self.idlePanel.MakeSodaStatsPanel()
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
        self.loginPanel = SodaLoginPanel(self, -1, wxPoint(0,0), self.GetSize())

        self.Bind(EVT_BUTTON, self.onDoLogin, id=ID_DOLOGIN)
        self.Bind(EVT_BUTTON, self.onLoginCancel, id=ID_CANCEL)

        self.loginPanel.Layout()
        self.loginPanel.Show(false)

    def beginLogin(self):
        self.loginPanel.Show(true)
        print "beginLogin"

    def endLogin(self):
        self.loginPanel.Clear()
        self.loginPanel.Show(false)
        print "endLogin"

    def onDoLogin(self, event):
        login = self.loginPanel.GetLogin()

        # If it fails, we'll stay here
        self.loginPanel.Clear()

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
        self.passwordPanel = SodaPasswordPanel(self, 
                                               -1, 
                                               wxPoint(0,0), 
                                               self.GetSize())

        self.Bind(EVT_BUTTON, self.onDoPassword, id=ID_DOPASSWORD)

        self.passwordPanel.Layout()
        self.passwordPanel.Show(false)

    def beginPassword(self):
        self.passwordPanel.SetStatusText('Authenticating ' + self.user, 'YELLOW')
        self.passwordPanel.Show(true)
        self.passwordCount = self.passwordLimit
        print "beginPassword"

    def endPassword(self):
        self.passwordPanel.Clear()
        self.passwordPanel.Show(false)
        print "endPassword"

    def onDoPassword(self, event):
        password = self.passwordPanel.GetPassword()
        self.passwordPanel.Clear()

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
        self.purchasePanel.Bind(EVT_BUTTON, self.onFpLearn, id=ID_FPLEARN)

        self.purchasePanel.Layout()
        self.purchasePanel.Show(false)


    def beginPurchase(self):
        # force the fp thing to go away.
        self.FPServVL.set("visible", None, "0")

        self.purchasePanel.SetStatusText('Ready for ' + self.user, 'GREEN')
        self.purchasePanel.SetUser(self.user)
        self.purchasePanel.SetBalance(self.balance)
        # These vars should be setup by the onLoginEvent
        self.updateTTLTimerLabel(STATE_PURCHASE)

        # Kick off the timer.
        self.TTLTimer.Start(1000)

        self.purchasePanel.Show(true)
        print "beginPurchase"

    def endPurchase(self):
        self.purchasePanel.Clear()
        self.TTLTimer.Stop()
        print "endPurchase"

    def onFpLearn(self, event):
        self.changeState(STATE_FPLEARN)

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
        self.purchasePanel.AddLog(event.item + " for " + monetize(event.price))

        print "Bought Event: " + event.item

    def onTtlEvent(self, event):
        self.timeout = int(event.timeout)
        print "Ttl Event"

    def onBalanceEvent(self, event):
        self.balance = int(event.balance)
        self.purchasePanel.SetBalance(self.balance)
        print "Balance Event"

    #
    # FP Panel
    #
    def makeFpPanel(self):
        self.fpPanel = SodaFPPanel(self,
                                   -1,
                                   wxPoint(0,0),
                                   self.GetSize())

        self.fpPanel.Bind(EVT_BUTTON, self.onFpCancel, id=ID_CANCEL)

        self.fpPanel.Layout()
        self.fpPanel.Show(false)

    def onFpCancel(self, event):
        self.changeState(STATE_PURCHASE)

    def beginFpLearn(self):
        print "beginFpLearn"
        self.fpPanel.SetStatusText('Learning FP for ' + self.user, 'BLUE')
        self.fpPanel.Show(True)
        self.TTLTimer.Start(1000)
        self.updateTTLTimerLabel(STATE_FPLEARN)
        self.bus.send(["LEARNSTART"])

        self.FPServVL.set("winx", None, "500")
        self.FPServVL.set("winy", None, "130")
        self.FPServVL.set("auto_hide", None, "0")
        self.FPServVL.set("visible", None, "1")
        # Set up FP Reader stuff

    def endFpLearn(self):
        print "endFpLearn"
        self.fpPanel.Show(False)
        self.fpPanel.Clear()
        self.TTLTimer.Stop()
        self.bus.send(["LEARNEND"])

        self.FPServVL.set("visible", None, "0")
        self.FPServVL.set("winx", None, "5")
        self.FPServVL.set("winy", None, "246")
        self.FPServVL.set("auto_hide", None, "1")
        self.FPServVL.set("auto_show", None, "1")

    def onFpEvent(self, event):
        # XXX
        if self.state != STATE_FPLEARN:
            self.changeState(STATE_FPLEARN)

        self.fpPanel.SetCount(event.count)
        self.fpPanel.SetMessage(event.msg)

        if event.complete == "1":
            self.changeState(STATE_PURCHASE)


    # Gui helper
    def updateTTLTimerLabel(self, state):
        if state == STATE_PURCHASE:
            self.purchasePanel.SetTTL(str(self.timeout))
        elif state == STATE_FPLEARN:
            self.fpPanel.SetTTL(str(self.timeout))
        else:
            print "mysterious timer event"

    def onTTLTimerFire(self, event):
        self.timeout = max(self.timeout - 1, 0)
        #if self.timeout <=  0:
        #    evt = LogoutEvent()
        #    wx.PostEvent(self, evt)

        self.updateTTLTimerLabel(self.state)




    #
    # ServIO callback handlers.
    #

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

    def handleUiFpNotice(self, data):
        evt = FpEvent(count=data[1],
                      msg=data[2],
                      complete=data[3])
        wx.PostEvent(self, evt)


class SodaApp(wxApp):
    def OnInit(self):
        self.bus = servio.ServIO("PYUI", "1.0")
        self.bus.defaultHandler(servio.noop_handler)

        frame = SodaFrame(NULL, -1, "Python Soda UI", self.bus)
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
        self.bus.watchMessage("UI-FP-NOTICE", frame.handleUiFpNotice)

        self.bus_thread = threading.Thread(target=self.bus.receive)
        self.bus_thread.start()

        return true

    def Exit(self):
        self.bus.exit()

app = SodaApp(0)
app.MainLoop()
app.Exit()
