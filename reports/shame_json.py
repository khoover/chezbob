#!/usr/bin/python3.4
"""Super-fast hacky way to support an updateable shaming dashboard."""

import configparser
import io
import json
import os.path
import psycopg2
import psycopg2.extras
import sys


CONFIG_REL_PATH = "../db.conf"
OUTFILE = "/git/www/json/shame.json"
ANNOUNCE_PATH = "/git/www/json/shame_screen.json"


DEBT_THRESHOLD = 15.0
DAYS_THRESHOLD = 28

HIGH_DEBT_QUERY = """
    SELECT
        username,
        nickname,
        balance,
        extract('days' from (now() - entered_wall)) as days_on_wall
    FROM users
    WHERE
        balance <= -{debt_threshold}
        AND (NOT disabled)
        AND (last_purchase_time > now() - INTERVAL '6 months')
    ORDER BY balance ASC
    LIMIT 20
"""

DELINQUENT_QUERY = """
    SELECT
        username,
        nickname,
        balance,
        extract('days' from (now() - entered_wall)) as days_on_wall
    FROM users
    WHERE
        (NOT disabled)
        AND entered_wall < now() - interval '{day_threshold} days'
        AND (last_purchase_time > now() - INTERVAL '12 months')
    ORDER BY balance ASC
    LIMIT 20
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
    return conn


def prepare_debtor_set(cursor, query, type_name, **formatting):
    cursor.execute(query.format(**formatting))
    debtors = []
    for i, row in enumerate(cursor):
        debtor = dict(row)
        debtor['balance'] = float(debtor['balance'])
        debtor['debt'] = "{:.2f}".format(-1 * debtor['balance'])
        debtor['index'] = i
        debtor['type'] = type_name
        debtors.append(debtor)
    return debtors


def generate_shame_json():
    config_file = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            CONFIG_REL_PATH)
    )

    conn = get_db(config_file)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    high_debt = prepare_debtor_set(
        cursor, HIGH_DEBT_QUERY, "high_value", debt_threshold=DEBT_THRESHOLD)
    delinquent = prepare_debtor_set(
        cursor, DELINQUENT_QUERY, "delinquent", day_threshold=DAYS_THRESHOLD)

    debtors = high_debt + delinquent

    data = {
        "debtors": debtors,
        "debt_threshold": DEBT_THRESHOLD,
        "days_threshold": DAYS_THRESHOLD,
    }

    with open(OUTFILE, 'w') as f:
        f.write(json.dumps(data))

    with open(ANNOUNCE_PATH, 'w') as f:
        if delinquent or high_debt:
            f.write(
                '{"url": "https://chezbob.ucsd.edu/shame_kiosk_simple.html",'
                ' "duration": ' + str(8 * len(debtors)) + ','
                ' "hold_tags": ["bobwall", "chezbob"]}\n')
        else:
            f.write('{}\n')

    # sys.stdout.write(json.dumps(data))


def main():
    return generate_shame_json()


if __name__ == "__main__":
    sys.exit(main())
