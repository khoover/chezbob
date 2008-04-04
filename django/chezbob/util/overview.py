"""Code for analyzing sales statistics and inventory shrinkage."""

import datetime, time, re, sys

from chezbob.bobdb.models import BulkItem, Inventory, Product, Order, OrderItem, ProductSource, TAX_RATE
from django.db import connection
cursor = connection.cursor()

date_end = datetime.date.today()
date_start = date_end - datetime.timedelta(days=90)

def summary():
    print "Summary: %s - %s" % (date_start, date_end)
    inventory_start = Inventory.get_inventory_estimate(date_start - datetime.timedelta(days=1), True)
    inventory_end = Inventory.get_inventory_estimate(date_end, True)

    sales = Inventory.get_sales(date_start, date_end)

    cursor.execute("""SELECT bulk_type_id, sum(quantity * number)
                      FROM order_items
                      WHERE order_id IN
                          (SELECT id FROM orders
                           WHERE date >= '%s' AND date <= '%s')
                      GROUP BY bulk_type_id""", (date_start, date_end))
    purchases = dict(cursor.fetchall())

    cursor.execute("""SELECT bulkid, AVG(products.price)
                      FROM products JOIN bulk_items USING (bulkid)
                      GROUP BY bulkid""")
    prices = dict(cursor.fetchall())

    profit = 0.0
    exp_profit = 0.0
    all_sales = 0.0

    for p in list(BulkItem.objects.order_by('description')):
        id = p.bulkid
        volume = sales.get(id, 0)
        losses = (purchases.get(id, 0) - sales.get(id, 0)) \
                 - (inventory_end[id]['estimate']
                      - inventory_start[id]['estimate'])
        if volume == 0 and losses == 0: continue
        shrinkage = float(losses) / (volume + losses)
        print p.description
        print "    Losses: %.1f%% (actual sales: %d)" % (shrinkage * 100.0, volume)
        print "    Prices: %.2f -> %.2f" % (p.unit_price(), prices[id])

        total_cost = (volume + losses) * p.unit_price()
        total_sales = volume * prices[id]

        print "    Profit: $%.2f (on sales $%.2f)" % (total_sales - total_cost, total_sales)

        profit += total_sales - total_cost
        exp_profit += volume * (prices[id] - p.unit_price())
        all_sales += total_sales

    print "Aggregate Sales: $%.2f" % (all_sales,)
    print "Total Profit: $%.2f" % (profit,)
    print "Expected Profit: $%.2f (no inventory shrinkage)" % (exp_profit,)
