"""Super-fast hacky way to support an updateable shaming dashboard."""

import ConfigParser
import StringIO
import json
import os.path
import psycopg2
import sys


CONFIG_REL_PATH = "../db.conf"


QUERY = """
    SELECT
        username, nickname, balance
    FROM users
    WHERE
        balance < -10
        AND (NOT disabled)
        AND (last_purchase_time > now() - INTERVAL '6 months')
    ORDER BY balance ASC
    LIMIT 15
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
    cursor.execute(QUERY)

    results = []
    for row in cursor:
        results.append(
            [row[1] if row[1] else row[0], "{:.2f}".format(-1 * row[2])])

    print json.dumps(results)


if __name__ == "__main__":
    sys.exit(main())

