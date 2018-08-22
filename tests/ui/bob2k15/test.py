#! /usr/bin/env python
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../lib/ui')

from bobui_2k15 import BobUI
import unittest

ui = BobUI('192.168.56.104')

class LoginOut(unittest.TestCase):
    def test_login(s):
        s.assertTrue(ui.at(ui.Login))
        ui.login('dev', '')
        s.assertTrue(ui.at(ui.MainPage))
        s.assertTrue(ui.user() == 'dev')
        ui.logout()
        s.assertTrue(ui.at(ui.Login))

    def tearDown(s):
        ui.close();

if (__name__ == '__main__'):
    unittest.main()
