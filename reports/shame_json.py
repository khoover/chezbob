#!/usr/bin/python
"""Super-fast hacky way to support an updateable shaming dashboard."""

import ConfigParser
import StringIO
import json
import os.path
import psycopg2
import sys


CONFIG_REL_PATH = "../db.conf"
OUTFILE = "/git/www/json/shame.json"
ANNOUNCE_PATH = "/git/www/json/wall_screen.json"


THRESHOLD = 15.00

QUERY = """
    SELECT
        username, nickname, balance
    FROM users
    WHERE
        balance <= -{threshold}
        AND (NOT disabled)
        AND (last_purchase_time > now() - INTERVAL '6 months')
    ORDER BY balance ASC
    LIMIT 20
"""


def get_db_info(config_file):
    config = ConfigParser.RawConfigParser()
    ini_str = '[DEFAULT]\n' + open(config_file, 'r').read()
    ini_fp = StringIO.StringIO(ini_str)

    config = ConfigParser.RawConfigParser()
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


def main():
    config_file = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            CONFIG_REL_PATH)
    )

    conn = get_db(config_file)
    cursor = conn.cursor()
    cursor.execute(QUERY.format(threshold=THRESHOLD))

    results = []
    for i, row in enumerate(cursor):
        results.append(
            [
                row[1],
                "{:.2f}".format(-1 * row[2]),
                row[0],
                i
            ]
        )

    data = {
        "debtors": results,
        "threshold": THRESHOLD,
    }

    with open(OUTFILE, 'w') as f:
        f.write(json.dumps(data))

    with open(ANNOUNCE_PATH, 'w') as f:
        if len(results):
            f.write(
                '{"url": "https://chezbob.ucsd.edu/shame_kiosk.html",'
                ' "duration": 30.0,'
                ' "hold": true}\n')
        else:
            f.write('{}\n')

    # sys.stdout.write(json.dumps(data))


if __name__ == "__main__":
    sys.exit(main())
