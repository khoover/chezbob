#!/usr/bin/python3.4
"""

This script takes in an HTML page on stdin, and outputs an order file as
expected by add_order.

It's hacky, but this part of Costco's UI changes often enough that you
shouldn't get too invested...

It uses the source of pages at, e.g.
https://www.costcobusinessdelivery.com/OrderStatusDetailsView?langId=-1&storeId=11301&catalogId=11701&orderId=275840140

It works at least as of 18-03-08.

"""

import re
import sys


def main():
    inp = sys.stdin.read()

    itemNos = re.findall("<p>Item&nbsp;(\d+)</p>", inp)
    costs = re.findall("<p>\$(\d|.+)</p>", inp)
    quants = re.findall(
        ('<!-- Show the Shipment details -->\s+<p class="body-copy">\s+'
         'Quantity Ordered\s+<span class="cust_ttlbox">(\d+)<'),
        inp)

    for item, quantity, cost in zip(itemNos, quants, costs):
        if item.endswith(u"000000"):
            continue

        print(item, quantity, '$' + cost)


if __name__ == "__main__":
    sys.exit(main())

