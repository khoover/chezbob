from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
from types import ClassType, MethodType

class Page:
    def __init__(s, ui):
        s._ui = ui;

class UI:
    def __init__(s, ip):
        s._ip = ip;
        s._dr = webdriver.Firefox()
        s._dr.get("http://%s:8080/ui/kiosk.html?type=0&id=0" % ip)
        s._pages = {}
        for n in dir(s):
            e = getattr(s,n)
            if (type(e) == ClassType and issubclass(e, Page)):
                s._pages[e] = e(s)

        s._cur_page = s.cur() 

    def cur(s):
        """ Find the current page. To do so we iterate over all pages.
            Note that one page may inherit from another, in which case
            we want to take the most specific page. If two unrelated
            pages both claim to be the current page, throw an error.
        """
        curP = None
        for p in s._pages.itervalues():
            if p.at():
                if curP:
                    if issubclass(curP.__class__, p.__class__):
                        pass;
                    elif issubclass(p.__class__, curP.__class__):
                        curP = p
                    else:
                        raise Exception("Both %s and %s claim to be current!" %
                            (str(curP), str(p)))
                else:
                    curP = p;
        return curP

    def at(s, page):
        """ Check if we are on a given page (by giving its string name) """
        return s._pages[page].at();

    def css(s, selector):
        """ Find an element on a page by its css selector """
        try:
            return s._dr.find_element_by_css_selector(selector)
        except NoSuchElementException:
            return None

    def visible(s, selector):
        e = s.css(selector)
        # WARNING (dbounov): is_displayed will return false if the element
        # is scrolled out of view. If the page doesn't fit in one window,
        # we will have problems!!
        return e.is_displayed()

    def has(s, selector):
        return s.css(selector) != None

    def __getattr__(s, name):
        cp = s.cur()
        try:
            attr = getattr(cp, name)
            if (type(attr) != MethodType or
                attr.__func__.func_name in ['at']):
                raise AttributeError()

            return attr
        except AttributeError:
            raise AttributeError()

    def close(s):
        s._dr.close()
        s._dr.quit()
