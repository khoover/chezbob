import select
import sys

import psycopg2
import psycopg2.extensions
import psycopg2.extras


def get_details(cur, id):
    cur.execute("SELECT * FROM TRANSACTIONS WHERE id = %s", [id])
    return cur.fetchone()


def get_detailed_details(cur, id):
    cur.execute(("SELECT t.*, u.*, p.*, t.barcode as t_barcode"
                 " FROM transactions t"
                 " INNER JOIN users u"
                 " ON t.userid = u.userid"
                 " LEFT OUTER JOIN products p"
                 " ON p.barcode = t.barcode"
                 " WHERE id = %s"), [id])
    return cur.fetchone()


def trunc(st, ln):
    if not st:
        return ''
    return st[:ln]


def print_transactions(curs, tid):
    result = get_detailed_details(curs, tid)
    format_line = "{:13} | {:40} | {:6} | {:8} | {:20} | {:20} | {:6} | {}"

    print(format_line.format(
        result['barcode'] if result['barcode'] else '',
        result['xacttype'][:40],
        result['xactvalue'],
        result['username'][:8],
        trunc(result['nickname'], 20),
        result['email'][:20],
        result['balance'],
        result['xacttime'].strftime("%x %X")
    ))


def watch_transactions(cbs):
    if type(cbs) != list:
        cbs = [cbs]

    conn = psycopg2.connect(dbname='bob', user='bob', host='localhost')
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    conn.set_client_encoding("utf-8")

    curs = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    curs.execute("LISTEN new_transactions;")

    while 1:
        if select.select([conn], [], [], 5) == ([], [], []):
            pass
        else:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                for cb in cbs:
                    cb(curs, int(notify.payload))
                #print(notify.pid, notify.channel, notify.payload)


def main():
    watch_transactions(print_transactions)

if __name__ == '__main__':
    sys.exit(main())
