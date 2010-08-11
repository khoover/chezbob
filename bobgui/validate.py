import wx
import re

user_re = re.compile("^[a-zA-Z]+$")
email_re = re.compile("^[A-Za-z0-9._%+-]+@[a-zA-Z0-9.-]+$")

def validateEmail(email):
    return email_re.match(email)

def warnEmail(parent, email):
    msg = "%s is not a valid email ([A-Za-z0-9._%%+-]+@[a-zA-Z0-9.-]+)" % email
    warning = wx.MessageDialog(parent, 
                              msg, msg,
                              wx.OK | wx.ICON_EXCLAMATION)
    warning.ShowModal()

def validateUserName(user):
    return user_re.match(user)

def warnUserName(parent, username):
    msg = "%s is not a valid username ([A-Za-z]+)" % username
    warning = wx.MessageDialog(parent, 
                              msg, msg,
                              wx.OK | wx.ICON_EXCLAMATION)
    warning.ShowModal()
