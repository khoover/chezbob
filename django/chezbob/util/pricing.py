"""Code for repricing items sold at Chez Bob."""

import datetime, time, re, sys

from chezbob.bobdb.models import BulkItem, Product, ProductSource
from django.db import connection
import django.db.transaction
cursor = connection.cursor()

markups = {
    1: 0.14,                    # Shelves
    2: 0.12,                    # Refrigerator
    3: 0.12,                    # Freezer
    4: 0.06,                    # Soda machine
    5: 0.16,                    # Terminal
    0: 0.16,                    # Unknown
}

def reprice(dry_run=False):
    def format_price_list(l):
        if len(l) == 0:
            return "??"
        p = sorted(set("%.2f" % (x,) for x in l))
        return ", ".join(p)

    def price_set(s):
        for b in s:
            markup = markups[b.floor_location.id]
            price = round(b.unit_price() * (1 + markup), 2)
            old_prices = [p.price for p in b.product_set.all()]
            print "%s\t%s\t%.2f\t%.3f" % (b.description, format_price_list(old_prices), price, b.unit_price())
            if not dry_run:
                for p in b.product_set.all():
                    p.price = price
                    p.save()

    print "Product\tOld Price\tNew Price\tCost"
    price_set(BulkItem.objects.filter(active=True).order_by('description'))
    print
    price_set(BulkItem.objects.filter(active=False).order_by('description'))
