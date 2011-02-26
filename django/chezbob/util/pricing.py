"""Code for repricing items sold at Chez Bob."""

import cgi, datetime, time, re, sys
from decimal import Decimal

from chezbob.bobdb.models import BulkItem, Product, ProductSource, HistoricalPrice
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

def dump_price_listing(out, update=True):
    today = datetime.date.today()

    def format_price_list(l):
        if len(l) == 0:
            return "??"
        p = sorted(set(map(str, l)))
        return ", ".join(p)

    out.write("<table class='tablesorter'><thead><tr>")
    for field in ['Product', 'Current Price', 'Previous Price', '% Change',
                  'Unit Cost']:
        out.write("<th>" + field + "</th>")
    out.write("</tr></thead>\n<tbody>\n")
    for b in BulkItem.objects.order_by('description'):
        markup = float(b.floor_location.markup)
        price = to_decimal(float(b.unit_price()) * (1 + markup))
        add_new_historical_price = True
        try:
            # The historical_prices table contains prices for items at various
            # points in the past.  Pull out the most recent two prices; since
            # we try not to insert consecutive entries at the same price at
            # least one of these should be different from the current price.
            # Choose the most recent price which differs from the current one
            # as the "old" price.
            old_prices = b.historicalprice_set.order_by('-date')[0:2]
            if price != old_prices[0].price:
                old_price = old_prices[0]
            else:
                old_price = old_prices[1]
                add_new_historical_price = False

            change = (float(price) / float(old_price.price) - 1) * 100
            if change != 0:
                change = "%.01f%%" % (change,)
            else:
                change = ""
            old_price = "$%.02f on %s" % (old_price.price, old_price.date)
        except:
            old_price = ""
            change = ""

        # If we are repricing items, and the price has changed since the last
        # repricing, write out a new record to the historical prices table.
        if update:
            for p in b.product_set.all():
                p.price = price
                p.save()
            if add_new_historical_price:
                b.historicalprice_set.filter(date__exact=today).delete()
                hp = HistoricalPrice(date=today, price=price, bulkid=b)
                hp.save()

        if b.active:
            out.write("<tr>")
            for f in [b.description, "$%.02f" % (price,), old_price, change,
                      "$%.04f" % (b.unit_price(),)]:
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
