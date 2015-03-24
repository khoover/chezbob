#! /usr/bin/env python

import os
import sys
import email
import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

def parseEmailOrder(emailText):
  msg = email.message_from_string(emailText)
  htmlPart = None
  # Given a (potentially forwarded) e-mail message, containing an order
  # Walk its mime parts looking for the ONLY text/html one
  for p in msg.walk():
    if p.get_content_type() == 'text/html':
      assert htmlPart == None
      htmlPart = p

  htmlContents = htmlPart.get_payload(decode=True)
  return parseOrder(htmlContents)

def _extractTable(tbl):
  """Given a simple bs table return a list with tuples with its contents"""
  res = []
  for row in tbl.tbody:
    if type(row) != Tag:
      continue
    res_row = []
    for cell in row.contents:
      if type(cell) != Tag or len(cell.contents) == 0:
        continue

      s = u''
      for i in cell.contents:
        if type(i) == Tag and i.name == "br":
          s += u'\n'
        elif type(i) == NavigableString:
          s += i
        else:
          print "Unexpected cell content:", i
          assert False

      res_row.append(s)
    res.append(res_row)
  return res

def _nonempty(s): return len(s.strip()) != 0

def skipEmptyStrings(l):
  return filter(lambda x: not (type(x) == NavigableString and len(x.strip()) == 0), l)

def _dictify(l):  return dict(map(lambda x: (x[0].strip(), x[1]), l))
        
def parseOrder(html):
  soup = BeautifulSoup(html)
  # The main sections of the order are several tables lieing at the following path
  tables = soup.body.table.tbody.tr.td.contents
  # tables[0] is the costco logo on the top left side
  # tables[1] is the order steps on the top right side
  # tables[2] contains the 3 tables at the top with order general info,
  # shipping address and email note
  orderInfoTbl = tables[2].contents[1].tr.contents[0].table
  shippingAddrTbl = tables[2].contents[1].tr.contents[1].table
  # tables[3] is just the opening "Dear Blahblahblah"
  # tables[4] is the e-mail text message "thank you for ordering..."
  # tables[5] is the big list of purchased items
  itemListTbl = tables[5]
  # tables[6] contains the order sum total at the bottom
  totalTbl = skipEmptyStrings(tables[6].tbody.tr.contents)[1]
  # tables[7] is the disclaimer at the bottom

  # Now first lets extract the general order info:
  orderInfo = _extractTable(orderInfoTbl)
  # Next shipping address:
  address = map(lambda x: x[0].strip(),  _extractTable(shippingAddrTbl.tbody.contents[2]))

  # Next lets get the list of items
  rawItems = _extractTable(itemListTbl.tbody.contents[0].contents[0].contents[0])
  # Some sanity checking
  rawItems[0:2] == [[u'Your Order'], \
                    [u'Qty', u'Description', u'Shipping Method', u'Price', u'Item Total']]
  rawItems = filter(lambda x: len(x) > 0, rawItems[2:])

  #Some helpers..
  has_item = re.compile("Item# (-?[0-9]+)")
  wsp = re.compile("\s")
  def isPrice(s):
    if s[0] != '$': return False
    try:
      f = float(s[1:])
      return True
    except:
      return False

  def isCostcoPrice(s):
    els = filter(_nonempty, wsp.split(s.strip()))
    if (len(els) == 1):
      return isPrice(els[0])
    elif (len(els) == 4):
      return isPrice(els[0]) and els[1] in [u'Before', u'After'] and isPrice(els[2]) and\
          els[3] == 'OFF'
    else:
      return False

  def isItemNum(s):
    if (s[0] == '-'):
      return s[1:].isdecimal()
    else:
      return s.isdecimal()

  # Sanity: Now we should be left with only valid rows
  def isValidRow(row):
    # First is the number of items
    if not (row[0].isdecimal()):  return False
    # Second is description that necessarily includes an item #
    if not (has_item.search(row[1])): return False
    if not isItemNum(has_item.search(row[1]).groups()[0]): return False
    # Third is the delivery method
    if not (row[2] == u'Business Delivery'):  return False
    # Fourth and Fifth are the single item price and total price
    if not (isCostcoPrice(row[3]) and isCostcoPrice(row[4])): return False
    return True

  for item in rawItems:
    try:
      assert isValidRow(item)
    except Exception, e:
      print item
      raise e

  def extractPrice(s):
    try:
      return float(s.strip()[1:].replace(',',''))
    except:
      print s
      raise

  # Next lets extract each row
  def extractCostcoPrice(s):
    els = filter(_nonempty, wsp.split(s.strip()))
    if (len(els) == 1):
      return extractPrice(els[0])
    else:
      return (extractPrice(els[0]), extractPrice(els[2]), els[1] == u'Before')

  def extractItem(row):
    return (int(row[0]), has_item.search(row[1]).groups()[0], row[1], \
        extractCostcoPrice(row[3]), extractCostcoPrice(row[4]))

  cookedItems = map(extractItem, rawItems)

  # In totals, things that get subtracted are held in ()
  def extractTotal(s):
    s = s.strip()
    if s[0] == '(':
      assert s[-1] == ')'
      return (extractPrice(s[1:-1]), False)
    else:
      return (extractPrice(s), True)

  totals = map(lambda r:  [r[0], extractTotal(r[1])], _extractTable(totalTbl))

  return (_dictify(orderInfo), address, cookedItems, _dictify(totals))

def orderPrice(price):
  if type(price) == float:
    return price
  else:
    return price[0]

def coupon(price):
  if type(price) == float:
    return 0 
  elif price[2]:
    return price[1]
  else:
    return 0

def floatEq(a,b,delta = 0.00001):
  return abs(a-b) < delta

def validOrder(order):
  """ Perform sanity checks on order """
  # Check total prices = num items X item price
  expCoupon = 0
  for item in order[2]:
    if not floatEq(item[0]*orderPrice(item[3]), orderPrice(item[4])):
      return False
    expCoupon += coupon(item[3]) * item[0]
  # Check coupons add up
  (totalCoupon, add) = order[3].get(u'Less Coupon Applied:', (0.0, False))
  assert not add 

  if not floatEq(expCoupon, totalCoupon):
    print "WARNING: Mismatch in expected coupon:", expCoupon, totalCoupon
#    return False

  # Check pre-tax totals
  expPreTax = sum([x[4] for x in order[2]])
  if not floatEq(expPreTax, order[3]['Subtotal:'][0]):
    print "Mismatch in expected total:", expPreTax, order[3]['Subtotal:']
    assert False;

  return True

if __name__ == "__main__":
  if (len(sys.argv) == 2):
    txt =open(sys.argv[1]).read()
  elif len(sys.argv) == 1:
    txt = sys.stdin.read()
  else:
    print "Usage: %s [<filename.email>]" % (sys.argv[0])
    sys.exit(-1)

  order = parseEmailOrder(txt)
  assert validOrder(order)
