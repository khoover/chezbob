# This was written haphazardly. My apologies for the bad coding.
# -Brown

from __future__ import print_function

#import argparse
import os
import re
import sys
import time
import unittest

# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
#from selenium.webdriver.common.keys import Keys
#from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException


LINE_PATTERN = re.compile(r"(\d)+\s+(.*)\s\(\#(\d+).*\)")

PATH_TO_FIREFOX46 = "/Applications/Firefox46.app/Contents/MacOS/firefox"

errors = []


class AddItem(unittest.TestCase):

    def parse_order(self, order_file):
        order = []
        # read in the lines of the order estimate
        order_lines = order_file.read().splitlines()
        if len(order_lines) < 1:
            print('ERROR: order file is empty')
            sys.exit()

        # parse each line, adding to dictionary of items to order
        # sample norm:  1    Arizona Peach Tea [15.5 oz] (#326523)
        # sample weird: 1    Apples (#21405, #49118)
        for i in order_lines:
            # Skip over blank lines nicely
            i = i.strip()
            if not i or i[0] == '#':
                continue

            match = LINE_PATTERN.match(i)
            if not match:
                sys.stderr.write((
                    "ERROR item parsing failed: {}\n"
                    "\nCorrect:  1   Peach Tea (#326523)'\n"
                    "Correct-ish: 1   Apple (#21405, #49118)'\n"
                    "INcorrect: 1   Apples (# 21405)'\n").format(
                        i))
                sys.exit()
                continue

            qty, name, itemNo = match.groups()

            # add to list of orders
            order.append((itemNo, qty, i))

        return order

    def handle_input(self):
        order_file = None

        # file names
        order_name = 'order_estimate.txt'
        creds_name = 'creds.txt'

        if os.path.isfile(order_name):
            order_file = open(order_name, 'r')
        else:
            print('ERROR order_estimate.txt does not exist')
            sys.exit()

        # make sure creds.txt exists
        if os.path.isfile(creds_name):
            creds_lines = open(creds_name).read().splitlines()
            if len(creds_lines) != 2:
                print('ERROR: creds.txt formatted wrong, should have two lines')
                sys.exit()
            else:
                username = creds_lines[0]
                password = creds_lines[1]
        else:
            print('ERROR creds.txt does not exist')
            sys.exit()

        # parse order
        order = self.parse_order(order_file)
        return username, password, order

    def setUp(self):
        #self.driver = webdriver.Chrome()
        self.driver = webdriver.Firefox()

        #binary = FirefoxBinary(PATH_TO_FIREFOX46)
        #self.driver = webdriver.Firefox(firefox_binary=binary)

        self.driver.implicitly_wait(2)
        self.base_url = "http://www.costcobusinessdelivery.com"
        self.verificationErrors = []
        self.accept_next_alert = True
        self.username, self.password, self.order = self.handle_input()

    def test_add_item(self):
        global errors

        from ipdb import launch_ipdb_on_exception

        with launch_ipdb_on_exception():
            driver = self.driver
            driver.get(self.base_url + "/")

            print("Attempting logon")

            # login start
            driver.find_element_by_id("header_sign_in").click()
            driver.find_element_by_id("logonId").click()
            driver.find_element_by_id("logonId").clear()
            driver.find_element_by_id("logonId").send_keys(self.username)
            driver.find_element_by_id("logonPassword_id").clear()
            driver.find_element_by_id("logonPassword_id").send_keys(self.password)
            driver.find_element_by_id("deliveryZipCode").clear()
            driver.find_element_by_id("deliveryZipCode").send_keys("92093")
            print("Submit")
            driver.find_element_by_css_selector(
                "#LogonFormBD input[type=submit]").click()
            # login done

            num_items = len(self.order)
            # ordering start
            for i, (itemNo, qty, name) in enumerate(self.order):
                line = "  ({:3}/{:<3})  {:2} of #{:<8} - {}".format(
                    i + 1, num_items, qty, itemNo, name)
                print(line)
                started = time.time()
                driver.get(self.base_url + "/OrderByItemsDisplayViewBD")
                #driver.find_element_by_id("headerOrderByItem").click()
                itemNumber = driver.find_element_by_css_selector(
                    "input[name=itemNumber]")
                itemNumber.clear()
                itemNumber.send_keys(itemNo)
                itemQuantity = driver.find_element_by_css_selector(
                    "input[name=itemQuantity]")
                itemQuantity.clear()
                itemQuantity.send_keys(qty)
                driver.find_element_by_id("obiAddToCartFtr").click()

                if self.is_element_present(
                        By.CSS_SELECTOR, 'div.text-error'):
                    sys.stderr.write(
                        "#### Error adding {} {}\n".format(qty, itemNo))
                    reason = self.driver.find_elements(
                        by=By.CSS_SELECTOR, value='div.text-error')[0].text
                    errors.append((line, reason))
                print("    Took {:4}".format(time.time() - started))
            # ordering done

    def is_element_present(self, how, what):
        try:
            elements = self.driver.find_elements(by=how, value=what)
        except NoSuchElementException:
            return False
        return len(elements) > 0

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException:
            return False
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
        finally:
            self.accept_next_alert = True

    def tearDown(self):
        # so browser won't close after going to cart
        #self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
    print("============= Errors encountered while adding:")
    for error, reason in errors:
        print(error, ":", reason)
