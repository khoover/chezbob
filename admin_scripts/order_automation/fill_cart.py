### This was written haphazardly. My apologies for the bad coding.
### -Brown

# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re, sys, argparse, os
from time import sleep

class AddItem(unittest.TestCase):

    def parse_order(self, order_file):
        order = {}
        # read in the lines of the order estimate
        order_lines = order_file.read().splitlines()
        if len(order_lines) < 1:
            print 'ERROR: order file is empty'
            sys.exit()

        # parse each line, adding to dictionary of items to order
        # sample norm:  1    Arizona Peach Tea [15.5 oz] (#326523) 
        # sample weird: 1    Apples (#21405, #49118)
        for i in order_lines:
            # I suppose a cool regex could go here, but I'm not cool
            item = i.split()
            # only operate on this line if first number is a digit
            if item[0].isdigit(): 
                qty = item[0]
                for piece in item:
                    if '#' in piece:
                        # oops I am cool
                        itemNo = re.sub("[^0-9]", "", piece) 
                        # add to list of orders
                        order[itemNo] = qty
                        if itemNo == '':
                            print 'ERROR ' + str(item)
                            sys.exit()
        return order

    def handle_input(self):
        order_file = None
        creds = False

        # file names
        order_name = 'order_estimate.txt'
        creds_name = 'creds.txt'

        # strings holding user's Costco creds
        username = ''
        password = ''

        # dictionary holding the order details, in the form: order[ItemNo] = Qty
        order = {}

        if os.path.isfile(order_name):
            order_file = open(order_name,'r')
        else:
            print 'ERROR order_estimate.txt does not exist'
            sys.exit()

        # make sure creds.txt exists
        if os.path.isfile(creds_name):
            creds_lines = open(creds_name).read().splitlines()
            if len(creds_lines) != 2:
                print 'ERROR: creds.txt formatted wrong, should have two lines'
                sys.exit()
            else:
                username = creds_lines[0]
                password = creds_lines[1]
        else:
            print 'ERROR creds.txt does not exist'
            sys.exit()

        # parse order
        order = self.parse_order(order_file)
        return username, password, order

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://www2.costco.com/Browse/QuickOrderEntry.aspx?whse=BD_578&lang=en-US"
        self.verificationErrors = []
        self.accept_next_alert = True
        self.username, self.password, self.order = self.handle_input()

    def test_add_item(self):
        driver = self.driver
        driver.get(self.base_url + "/Browse/QuickOrderEntry.aspx?whse=BD_578&lang=en-US")
        # The first time you go, it will not work. Costco has to set a cookie I believe
        driver.get(self.base_url + "/Browse/QuickOrderEntry.aspx?whse=BD_578&lang=en-US")

        # login start
        driver.find_element_by_css_selector("img[alt=\"LOGIN\"]").click()
        driver.find_element_by_id("_ctl0_EmailAddress").clear()
        driver.find_element_by_id("_ctl0_EmailAddress").send_keys(self.username)
        driver.find_element_by_id("_ctl0_Password").clear()
        driver.find_element_by_id("_ctl0_Password").send_keys(self.password)
        driver.find_element_by_id("_ctl0_SubmitLogin").click()
        # login done

        # ordering start
        for itemNo, qty in self.order.iteritems():
            driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_ItemNo").clear()
            driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_ItemNo").send_keys(itemNo)
            driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_Qty").clear()
            driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_Qty").send_keys(qty)
            driver.find_element_by_id("QuickOrderEntry1_AddToOrder1").click()
            # add a little pause here??
        # ordering done

        # test order
        # driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_ItemNo").clear()
        # driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_ItemNo").send_keys('1')
        # driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_Qty").clear()
        # driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_Qty").send_keys('1')
        # driver.find_element_by_id("QuickOrderEntry1_AddToOrder1").click()
        # test order done

        # go to cart
        driver.find_element_by_id("TopNav1_ViewCartLink").click()

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        # so browser won't close after going to cart
        #self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
