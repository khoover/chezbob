from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
from types import ClassType, MethodType
from ui import Page, UI

class BobUI(UI):
    class Login(Page):
        def at(s):
            return s._ui.visible("#username") and \
                   s._ui.visible("#password") and \
                   s._ui.visible("input.btn")

        def login(s, username, password):    
            s._ui.css('#username').send_keys(username)
            s._ui.css('#password').send_keys(password)
            s._ui.css('input.btn').click()

    class LoggedIn(Page):
        def at(s):
            return s._ui.visible('.username')
        def user(s):
            return s._ui.css('.username').text
        def timeout(s):
            t = s._ui.css('.timeout')
            if (not t): return None

            if t.text == '':
                return None
            else:
                assert(t.text.endswith('s'))
                int(t.text[:-1])

        def logout(s):
            s._ui.css('#logoutbtn').click();

    class MainPage(LoggedIn):
        def at(s):
            return BobUI.LoggedIn.at(s) and \
                s._ui.visible('#otheritemsbtn') and \
                s._ui.visible('#optionsbtn') 
