# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re

class AddItem(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://www2.costco.com/Browse/QuickOrderEntry.aspx?whse=BD_578&lang=en-US"
        self.verificationErrors = []
        self.accept_next_alert = True
    
    def test_add_item(self):
        driver = self.driver
        driver.get(self.base_url + "/Browse/QuickOrderEntry.aspx?whse=BD_578&lang=en-US")
        # The first time you go, it will not work. Costco has to set a cookie I believe
        driver.get(self.base_url + "/Browse/QuickOrderEntry.aspx?whse=BD_578&lang=en-US")
        driver.find_element_by_css_selector("img[alt=\"LOGIN\"]").click()
        driver.find_element_by_id("_ctl0_EmailAddress").clear()
        driver.find_element_by_id("_ctl0_EmailAddress").send_keys("brown.farinholt@gmail.com")
        driver.find_element_by_id("_ctl0_Password").clear()
        driver.find_element_by_id("_ctl0_Password").send_keys("WRONGPASSWORD")
        driver.find_element_by_id("_ctl0_SubmitLogin").click()
        driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_ItemNo").clear()
        driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_ItemNo").send_keys("1")
        driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_Qty").clear()
        driver.find_element_by_id("QuickOrderEntry1_QuickOrderList__ctl1_Qty").send_keys("1")
        driver.find_element_by_id("QuickOrderEntry1_AddToOrder1").click()
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
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
