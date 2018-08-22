"""A few convenience functions for getting the database handles and cursors."""

import configparser
import io
import os

import psycopg2
import psycopg2.extras


DEFAULT_CONFIG_PATH = os.environ.get("CHEZBOB_DB_PATH", "/git/db.conf")

_db = None


def get_db_credentials(config_file):
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


def get_cursor(conn=_db):
    if not conn:
        conn = get_conn()
    return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


def get_conn(config_file=DEFAULT_CONFIG_PATH):
    global _db
    if not _db:
        creds = get_db_credentials(config_file)
        _db = psycopg2.connect(**creds)
        _db.set_client_encoding("UTF-8")
    return _db

