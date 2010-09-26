"""Code for repricing items sold at Chez Bob."""

import datetime, time, re, sys
from decimal import Decimal

from chezbob.bobdb.models import BulkItem, Product, ProductSource
from django.db import connection
import django.db.transaction
cursor = connection.cursor()

markups = {
    1: 0.10,                    # Shelves
    2: 0.11,                    # Refrigerator
    3: 0.12,                    # Freezer
    4: 0.05,                    # Soda machine
    5: 0.20,                    # Terminal
    0: 0.12,                    # Unknown
}

def to_decimal(f):
    """Convert a floating-point value to a decimal.

    The result has two digits after the decimal point, suitable for use as a
    currency value."""

    return Decimal(str(f)).quantize(Decimal("0.00"))
def reprice(dry_run=False):
    def format_price_list(l):
        if len(l) == 0:
            return "??"
        p = sorted(set(map(str, l)))
        return ", ".join(p)

    def price_set(s):
        for b in s:
            markup = markups[b.floor_location.id]
            price = to_decimal(float(b.unit_price()) * (1 + markup))
            old_prices = [p.price for p in b.product_set.all()]
            print "%s\t%s\t%s\t%s" % (b.description, format_price_list(old_prices), price, b.unit_price())
            if not dry_run:
                for p in b.product_set.all():
                    p.price = price
                    p.save()

    print "Product\tOld Price\tNew Price\tCost"
    price_set(BulkItem.objects.filter(active=True).order_by('description'))
    print
    price_set(BulkItem.objects.filter(active=False).order_by('description'))
