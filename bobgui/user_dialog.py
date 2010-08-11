import wx
import validate

class EmailValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)

    def Clone(self):
        return EmailValidator()

    def Validate(self, win):
        val = self.GetWindow().GetValue()
        email_ok = validate.validateEmail(val)

        if not email_ok:
            validate.warnEmail(self.GetWindow(), val)

        return email_ok

    def TransferToWindow(self):
        return True
    def TransferFromWindow(self):
        return True

class UserValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)

    def Clone(self):
        return UserValidator()

    def Validate(self, win):
        val = self.GetWindow().GetValue()
        user_ok = validate.validateUserName(val)

        if not user_ok:
            validate.warnUserName(self.GetWindow(), val)

        return user_ok

    def TransferToWindow(self):
        return True
    def TransferFromWindow(self):
        return True



class UserDialog(wx.Dialog):
    """
    A Dialog to enter email information for the initial account
    creation.
    """


    def __init__(self, parent, ID, title, username,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, 
                          parent=parent, 
                          title=title,
                          style=style,
                          pos=pos)

        windowSize = self.GetVirtualSize()

        topSizer = wx.BoxSizer(wx.VERTICAL)
        boxSizer = wx.BoxSizer(wx.VERTICAL)

        topSizer.Add(boxSizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

        noticeTxt = "We did not find the login information for %s." % username
        notice = wx.StaticText(self, -1, noticeTxt, style=wx.ALIGN_LEFT)

        enterTxt = "If you do not already have an account, fill in the form below to create one"
        enter = wx.StaticText(self, -1, enterTxt, style=wx.ALIGN_LEFT)

        enter.Wrap(windowSize.GetWidth())

        userNameLabel = wx.StaticText(self, -1, "Username: ")

        self.userNameInput = wx.TextCtrl(self,
                                        -1,
                                        username,
                                        wx.DefaultPosition,
                                        wx.Size(300, -1),
                                        validator=UserValidator())

        emailLabel = wx.StaticText(self, -1, "Email: ")

        self.emailInput = wx.TextCtrl(self, 
                                     -1, 
                                     "",
                                     wx.DefaultPosition,
                                     wx.Size(300, -1),
                                     validator=EmailValidator())

        boxSizer.Add(notice, wx.ALIGN_CENTER)
        boxSizer.Add(enter, wx.ALIGN_CENTER)

        dataSizer = wx.FlexGridSizer(2, 2, 5, 10)

        dataSizer.Add(userNameLabel)
        dataSizer.Add(self.userNameInput)

        dataSizer.Add(emailLabel)
        dataSizer.Add(self.emailInput)

        boxSizer.AddSpacer(wx.Size(10,10))
        boxSizer.Add(dataSizer, wx.ALIGN_LEFT)

        boxSizer.AddSpacer(wx.Size(10,10))

        boxSizer.Add(wx.StaticLine(self, 
                                  -1, 
                                  size = wx.Size(windowSize.GetWidth(),-1)), 
                                  wx.ALL, 
                                  5)

        boxSizer.AddSpacer(wx.Size(10,10))

        buttons = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        buttons.Realize()

        boxSizer.Add(buttons)

        self.SetSizer(topSizer)
        self.Fit()

        self.emailInput.SetFocus()

    def GetUserName(self):
        return self.userNameInput.GetLineText(0)

    def GetEmail(self):
        return self.emailInput.GetLineText(0)
