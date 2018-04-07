#!/usr/bin/python3.4
"""Quick hacky script to estimate for what we should order from Costco.

Output a file to pass to the order automation script.

Current strategy:
    - We estimate demand for the next order period (period between orders) by
      using the demand from the previous order period.
    - We do that by taking however much of each product we've sold since last
      time we got an order. We assume we'll have similar demand going forward.
      We add an extra quarter-case just in case demand exceeds expectations.
    - First, we calculate current inventory
    - We then project forward what our expected inventory would be, given that
      assumed demand and the current inventory.
    - For each product where the projected inventory is negative, we need to
      buy some of that product. We buy however many cases we need to in order
      to keep projected inventory positive.
    - This always buys at least one case if we're out of inventory on a
      product.  This is a stopgap in case we were out of a product for the
      entirety of an order period-- this occasionally happens when we're out of
      a product and so is Costco.

"""

import math
import sys

import psycopg2
import psycopg2.extras


# What was the MOST RECENT inventory for each item?
LAST_INVENTORY_VIEW = """
create or replace temporary view last_inventory as
select date, bulkid, units from (
        SELECT
            date,
            bulkid,
            units,
            rank() over (partition by bulkid order by date desc) as r
        from inventory
        where bulkid in (select bulkid from bulk_items where active)
        ) s1
where r = 1
"""

# Represents how many of an item we've purchased since the last inventory of it
RECENT_ORDERS_VIEW = """
create or replace temporary view recent_orders as
select min(order_date) as since, bulkid, sum(units) as units
from (
    select
        o.date as order_date,
        li.date AS last_inventoried,
        quantity*number as units,
        bulk_type_id as bulkid
    from orders o
        inner join order_items oi
            on oi.order_id = o.id
        left outer join last_inventory li
        on bulk_type_id = bulkid
    ) s1
where (case
        when last_inventoried is null then true
        else order_date > last_inventoried end)
group by bulkid
"""

# Represents how many of an item we've sold since the most recent inventory
RECENT_SALES_VIEW = """
create or replace temporary view recent_sales as
select min(date) as since, max(date) as most_recent, bulkid, count(*) as units
from (
    select
        xacttime as date,
        li.date AS last_inventoried,
        p.bulkid
    from transactions t
        inner join products p
            on p.barcode = t.barcode
        left outer join last_inventory li
        on li.bulkid = p.bulkid
    ) s1
where ( case
    when last_inventoried is null then true
    else date > last_inventoried end)
group by bulkid
"""

CURRENT_INVENTORY_VIEW = """
create or replace temporary view current_inventory as
select
    i.date,
    (case when i.bulkid is null then s.bulkid else i.bulkid end) as bulkid,
    (case when i.units is null then 0 else i.units end)
        + (case when o.units is null then 0 else o.units end)
        - (case when s.units is null then 0 else s.units end)
        AS remaining,
    i.units as n_inventoried,
    (case when o.units is null then 0 else o.units end) as n_ordered,
    (case when s.units is null then 0 else s.units end) as n_sold,
    s.most_recent as most_recent_sale
    from last_inventory i
        full outer join recent_sales s on s.bulkid = i.bulkid
        left outer join recent_orders o on o.bulkid =
            (case when i.bulkid is null then s.bulkid else i.bulkid end)
    order by remaining asc
"""

RECENT_SALES_QUERY = """
SELECT
    p.bulkid,
    bi.description,
    bi.quantity as case_size,
    count(distinct t.id) as n_sales
FROM products p
    INNER JOIN bulk_items bi ON bi.bulkid = p.bulkid
    LEFT OUTER JOIN (
        SELECT *
        FROM transactions
        WHERE
            xacttime > (
                SELECT date FROM orders
                WHERE sourceid IS NULL OR sourceid = 1
                ORDER BY date DESC
                LIMIT 1
            )
    ) t
    ON p.barcode = t.barcode
WHERE bi.active AND bi.source = 1
GROUP BY p.bulkid, bi.quantity, bi.description
    """


def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


def get_inventory(conn):

    cursor = get_cursor(conn)
    cursor.execute(RECENT_SALES_QUERY)
    bi_details = dict()
    for row in cursor:
        row = dict(row)
        bi_details[row['bulkid']] = row

    cursor.execute(LAST_INVENTORY_VIEW)
    cursor.execute(RECENT_ORDERS_VIEW)
    cursor.execute(RECENT_SALES_VIEW)
    cursor.execute(CURRENT_INVENTORY_VIEW)
    cursor.execute("SELECT * FROM current_inventory order by bulkid")
    for row in cursor:
        row = dict(row)
        b_id = row['bulkid']

        if b_id not in bi_details:
            continue

        row['proj_inv'] = row['remaining'] - bi_details[b_id]['n_sales']
        to_buy = 0 if row['remaining'] > 0 else 1
        if row['proj_inv'] <= 0:
            to_buy = math.ceil(
                -row['proj_inv'] / bi_details[b_id]['case_size'] + .25)
        if to_buy:
            print("{:<4} {}".format(to_buy, bi_details[b_id]['description']))


def main():
    conn = psycopg2.connect(dbname='bob', user='bob', host='localhost')
    get_inventory(conn)

if __name__ == "__main__":
    sys.exit(main())

