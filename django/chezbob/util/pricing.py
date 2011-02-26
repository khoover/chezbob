"""Code for repricing items sold at Chez Bob."""

import cgi, datetime, time, re, sys
from decimal import Decimal

from chezbob.bobdb.models import BulkItem, Product, ProductSource
from django.db import connection
import django.db.transaction
cursor = connection.cursor()

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
            markup = float(b.floor_location.markup)
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

def dump_price_listing(out):
    def format_price_list(l):
        if len(l) == 0:
            return "??"
        p = sorted(set(map(str, l)))
        return ", ".join(p)

    out.write("<table class='tablesorter'><thead><tr><th>Product</th><th>Old Price</th><th>New Price</th><th>Cost</th><th>% Change</th></tr></thead>\n")
    out.write("<tbody>\n")
    for b in BulkItem.objects.filter(active=True).order_by('description'):
        markup = float(b.floor_location.markup)
        price = to_decimal(float(b.unit_price()) * (1 + markup))
        old_prices = [p.price for p in b.product_set.all()]
        out.write("<tr>")
        try:
            change = (float(price) / float(old_prices[0]) - 1) * 100
            change = "%.1f%%" % (change,)
        except:
            change = ""
        for f in [b.description, format_price_list(old_prices),
                  price, b.unit_price(), change]:
            out.write("<td>" + cgi.escape(str(f)) + "</td>")
        out.write("</tr>\n")
    out.write("""</tbody></table>
<script type="text/javascript">
// <![CDATA[
$(document).ready(function() {
  $(".tablesorter").tablesorter();
}
// ]]>
</script>
""")
