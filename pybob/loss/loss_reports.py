#!/usr/bin/python3.4
"""Generate a loss report. Call with -h for details."""
import argparse
import configparser
import io
import os
import os.path
import psycopg2
import psycopg2.extras
import re
import sys

from datetime import datetime

CONFIG_PATH = "/git/db.conf"

END_BIT = re.compile(" \(#.*")

INVENTORY_QUERY = """
select * from (
    select
        i1.bulkid,
        i2.date as start,
        i1.date as end,
        i2.units as start_units,
        i1.units as end_units,
        rank() over (partition by i1.bulkid order by i2.date desc) as r
    from inventory i1
        inner join inventory i2 on i1.bulkid = i2.bulkid and i1.date > i2.date
        inner join bulk_items bi on bi.bulkid = i1.bulkid
    where
        i1.date::date = %s
        and bi.floor_location not in %s
    order by i1.bulkid desc
) s where s.r = 1
"""


def get_db_info(config_file):
    config = configparser.RawConfigParser()
    ini_str = '[DEFAULT]\n' + open(config_file, 'r').read()
    ini_fp = io.StringIO(ini_str)

    config = configparser.RawConfigParser()
    config.readfp(ini_fp)

    return {
        "host": config.get(
            'DEFAULT', 'DATABASE_HOST').strip().replace('"', ''),
        "user": config.get(
            'DEFAULT', 'DATABASE_USER').strip().replace('"', ''),
        "database": config.get(
            'DEFAULT', 'DATABASE_NAME').strip().replace('"', ''),
    }


def get_db(config_file):
    conninfo = get_db_info(config_file)
    conn = psycopg2.connect(**conninfo)
    conn.set_client_encoding("UTF-8")
    return conn


def get_cursor(db):
    return db.cursor(cursor_factory=psycopg2.extras.DictCursor)


def parse_args():

    def DateStamp(x):
        return datetime.strptime(x, "%Y-%m-%d").date()

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--date", type=DateStamp,
                       help="Date (YYYY-MM-DD) to generate report for")

    group.add_argument("--list_dates", action='store_true',
                       help="List dates")
    parser.add_argument("-S", '--exclude_soda', action='store_true',
                        help="Exclude items that live in the soda machine.")

    return parser.parse_args()


ORDER_QUERY = """
SELECT SUM(quantity * number)
FROM order_items oi INNER JOIN orders o
    ON o.id = oi.order_id
WHERE
    bulk_type_id = %s
    AND date > %s
    AND date < %s
"""


def get_n_ordered(conn, bulkid, start, end):
    cursor = get_cursor(conn)
    cursor.execute(ORDER_QUERY, (bulkid, start, end))
    if not cursor.rowcount:
        return 0
    res = cursor.fetchone()
    if res[0] is None:
        return 0
    return res[0]


SALES_QUERY = """
SELECT COUNT(*)
FROM transactions
WHERE
    barcode IN (SELECT barcode FROM products WHERE bulkid = %s)
    AND xacttime > %s AND xacttime < %s
;
"""


def get_n_sold(conn, bulkid, start, end):
    cursor = get_cursor(conn)
    cursor.execute(SALES_QUERY, (bulkid, start, end))
    if not cursor.rowcount:
        return 0
    return cursor.fetchone()[0]


def get_item_details(conn, bulkid):
    cursor = get_cursor(conn)
    QUERY = """
    SELECT
        bi.*,
        ((1+markup)*price/quantity)::numeric(6,2) as each
    FROM bulk_items bi INNER JOIN floor_locations fl
        ON fl.id = bi.floor_location
    WHERE bulkid = %s
    """
    cursor.execute(QUERY, (bulkid,))
    if not cursor.rowcount:
        return None
    return cursor.fetchone()


def print_inventory_dates(conn):
    cursor = get_cursor(conn)
    QUERY = """
    SELECT
        DISTINCT date::date
    FROM inventory
    ORDER BY date::date DESC limit 10
    """
    cursor.execute(QUERY)
    for row in cursor:
        print(row[0])


def main():
    config_file = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            CONFIG_PATH)
    )

    conn = get_db(config_file)

    args = parse_args()

    if args.list_dates:
        print_inventory_dates(conn)
        return

    exclude_set = {999}
    if args.exclude_soda:
        exclude_set.add(4)

    cursor = get_cursor(conn)
    cursor.execute(INVENTORY_QUERY, (args.date, tuple(exclude_set)))

    # There are better ways that aren't as query-heavy, but this is easy
    losses = []
    for item in cursor:
        #pprint(dict(item))
        n_sold = get_n_sold(conn, item['bulkid'], item['start'], item['end'])
        n_added = get_n_ordered(
            conn, item['bulkid'], item['start'], item['end'])
        expected = item['start_units'] - n_sold + n_added
        actual = item['end_units']
        loss = expected - actual
        if loss:
            details = get_item_details(conn, item['bulkid'])
            losses.append((loss, item['end'], item['start'], details))

    if losses:
        print("Loss report for:", args.date)
        print()

    def keyfunc(i):
        #return -i[0] * i[3]['each']
        return (-i[0], (i[1] - i[2]).days, i[3]['description'])

    TABLE_FMT = "{items:>4} | {days:4} | {total:6.2f} | {description:<60}"
    header = TABLE_FMT.format(
        items="#", days="Days", total=0, description="Description")
    print(header)
    print("-" * len(header))
    for loss, end, start, details in sorted(losses, key=keyfunc):
        print(TABLE_FMT.format(
            items=loss,
            days=(end - start).days,
            total=details['each'] * loss,
            description=END_BIT.sub("", details['description'])))


if __name__ == "__main__":
    sys.exit(main())
