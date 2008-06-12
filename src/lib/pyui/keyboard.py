from wxPython.wx import *
from pyui.config import *

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
