"""Simple code for estimating the value of Chez Bob inventory.

Using actual inventories taken, plus records of purchases and sales, estimate
the daily value of the Chez Bob inventory.  Additionally, estimate cost of
goods sold, profits, and shrinkage.
"""

import datetime, time, re, sys

from chezbob.bobdb.models import BulkItem, Inventory, Product, Order, OrderItem, ProductSource, TAX_RATE
from django.db import connection
cursor = connection.cursor()

ONE_DAY = datetime.timedelta(days=1)
price_estimates = {}

def extract(seq, date):
    while seq != []:
        if seq[0][0] > date: return
        yield seq.pop(0)

def check_item(inv, bulkid):
    if bulkid not in inv:
        price = price_estimates.get(bulkid, 0.0)
        inv[bulkid] = {'count': 0, 'cost': 0.0, 'price': price}

def item_name(bulkid):
    return BulkItem.objects.get(bulkid=bulkid).description

def summary(start, end=None, fp=None):
    if end is None:
        end = datetime.date.today()

    # For each item, a dictionary:
    #   count: number of that item currently in the inventory
    #   cost: total cost basis for all the items
    #   price: cost/count, the average cost per item
    inventory = {}

    print "Report range: %s - %s" % (start, end)

    cursor.execute("""SELECT i.bulk_type_id,
                             (cost_taxable * %s + cost_nontaxable) / quantity
                      FROM orders o JOIN order_items i ON (o.id = i.order_id)
                      WHERE o.date < '%s'
                      ORDER BY o.date DESC""",
                   (1 + TAX_RATE, start))
    for (bulkid, price) in cursor.fetchall():
        if bulkid not in price_estimates: price_estimates[bulkid] = price

    purchases = cursor.fetchall()
    for (k, v) in Inventory.get_inventory_estimate(start - ONE_DAY,
                                                   True).items():
        check_item(inventory, k)
        inventory[k]['count'] = v['estimate']
        inventory[k]['cost'] = v['estimate'] * inventory[k]['price']

    cursor.execute("""SELECT a.date, p.bulkid, SUM(a.quantity), SUM(a.price)
                      FROM aggregate_purchases a JOIN products p
                          USING (barcode)
                      WHERE a.date >= '%s' AND a.date <= '%s'
                      GROUP BY a.date, p.bulkid
                      ORDER BY a.date""", (start, end))
    sales = cursor.fetchall()

    cursor.execute("""SELECT o.date, i.bulk_type_id, i.quantity * i.number,
                             i.number * (cost_taxable * %s + cost_nontaxable)
                      FROM orders o JOIN order_items i ON (o.id = i.order_id)
                      WHERE o.date >= '%s' AND o.date <= '%s'
                      ORDER BY o.date""",
                   (1 + TAX_RATE, start, end))
    purchases = cursor.fetchall()

    cursor.execute("""SELECT date, bulkid, units
                      FROM inventory2
                      WHERE date >= '%s' AND date <= '%s'
                      ORDER BY date""", (start, end))
    inventories = cursor.fetchall()

    if fp is not None:
        fp.write("# Date\tInventory\tLosses\n")

    date = start
    while date <= end:
        print "Date: %s" % (date,)
        sales_total = 0.0
        sales_cost = 0.0
        new_inventory = 0.0
        losses = 0.0

        updated = set()

        for p in extract(purchases, date):
            #print "Purchase:", p
            (_, bulkid, count, cost) = p
            if bulkid is None: continue
            check_item(inventory, bulkid)
            inv = inventory[bulkid]
            inv['count'] += count
            inv['cost'] += cost
            new_inventory += cost
            updated.add(p[1])

        for s in extract(sales, date):
            #print "Sale:", s
            (_, bulkid, count, cost) = s
            if bulkid is None: continue
            check_item(inventory, bulkid)
            inv = inventory[bulkid]
            if inv['count'] == 0:
                cogs = 0.0
            else:
                cogs = count * (inv['cost'] / inv['count'])
            inv['cost'] -= cogs
            inv['count'] -= count
            #print "Profit: %.2f = %.2f - %.2f" % (cost - cogs, cost, cogs)
            if cost is not None:
                sales_total += cost
            sales_cost += cogs
            updated.add(s[1])

        for bulkid in updated:
            inv = inventory[bulkid]
            if inv['count'] < 0:
                print "WARNING: %s has negative count %d" \
                    % (item_name(bulkid), inv['count'])
            elif inv['count'] > 0:
                inv['price'] = inv['cost'] / inv['count']

        for i in extract(inventories, date):
            #print "Inventory:", i
            (_, bulkid, count) = i
            check_item(inventory, bulkid)
            inv = inventory[bulkid]
            if count != inv['count']:
                qty = inv['count'] - count
                print "    LOSS: $%.2f %s (expected %d, had %d)" \
                    % (qty * inv['price'], item_name(bulkid),
                       inv['count'], count)
                inv['count'] = count
                inv['cost'] -= qty * inv['price']
                losses += qty * inv['price']

        inventory_value = sum(inv['cost'] for inv in inventory.values())

        print "  Value %.2f (sales %.2f @ %.2f, new %.2f, losses %.2f)" \
            % (inventory_value, sales_cost, sales_total, new_inventory, losses)

        if fp is not None:
            fp.write("%s\t%.2f\t%.2f\n" % (date, inventory_value, losses))

        date += ONE_DAY

    print
    print "Final Inventory:"
    for (bulkid, inv) in inventory.items():
        if inv['count'] == 0: continue
        print "%6d %s (average cost: %.2f)" \
            % (inv['count'], item_name(bulkid), inv['price'])
