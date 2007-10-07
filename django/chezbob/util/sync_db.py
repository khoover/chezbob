"""Utility code for to synchronize the accounting ledger with transactions.

Read the transaction data from the traditional Chez Bob database tables, and
insert daily aggregate amounts into the main finance ledger.
"""

import datetime, time, re, sys

from chezbob.finance.models import Account, Split, Transaction, DepositBalances

dry_run = False

# Keep this synchronized with any changes to the account list in the database.
acct_bank = Account.objects.get(id=1)
acct_cash = Account.objects.get(id=7)
acct_deposits = Account.objects.get(id=2)
acct_donations = Account.objects.get(id=12)
acct_purchases = Account.objects.get(id=4)
acct_social_restricted = Account.objects.get(id=21)
acct_social_donations = Account.objects.get(id=20)
acct_writeoff = Account.objects.get(id=13)

# A description of the transactions that should automatically be created to
# reflect various types of activity.  In each list, the first item is the
# description, followed by a list of splits to include, as (multiplier,
# account) pairs.
auto_transactions = {
    'deposit':    ["Deposits", (+1, acct_cash), (-1, acct_deposits)],
    'donate':     ["Donations", (+1, acct_deposits), (-1, acct_donations)],
    'purchase':   ["Purchases", (+1, acct_deposits), (-1, acct_purchases)],
    'socialhour': ["Social Hour Donations",
                   (+1, acct_deposits), (-1, acct_social_donations),
                   (+1, acct_social_restricted), (-1, acct_bank)],
    'writeoff':   ["Debt Written Off",
                   (+1, acct_writeoff), (-1, acct_deposits)],
}

def insert_transaction(date, type, amount):
    info = auto_transactions[type]

    print "Insert %s, %.2f" % (info[0], amount / 100.0)

    if dry_run:
        return

    t = Transaction(date=date, description=info[0], auto_generated=True)
    t.save()
    for i in info[1:]:
        amt = (i[0] * amount) / 100.0
        s = Split(transaction=t, account=i[1], amount=amt)
        s.save()

# A running total of Bank of Bob liabilities (in cents)
bob_liabilities = 0

def update_day(date, amounts):
    old_transactions = list(Transaction.objects.filter(date=date,
                                                       auto_generated=True))

    # Should separated Bank of Bob liabilities (positive/negative) be
    # recomputed?
    update_bob_liabilities = False
    try:
        d = DepositBalances.objects.get(date=date)
        if int(round(100 * (d.positive - d.negative))) != bob_liabilities:
            update_bob_liabilities = True
    except DepositBalances.DoesNotExist:
        update_bob_liabilities = True

    for ty in sorted(amounts.keys()):
        info = auto_transactions[ty]

        # Search for an existing transaction, so we can update only if needed
        old = None
        for o in old_transactions:
            if o.description == info[0]:
                old = o
                break

        if old is not None:
            old_transactions.remove(old)

            # Compare the existing transaction with the actual amount needed.
            mismatch = False
            splits = list(old.split_set.all())
            needed_splits = info[1:]
            for s in splits:
                amt = int(round(s.amount * 100))
                if amt == amounts[ty]:
                    factor = +1
                elif amt == -amounts[ty]:
                    factor = -1
                else:
                    mismatch = True
                    break
                if (factor, s.account) in needed_splits:
                    needed_splits.remove((factor, s.account))
                else:
                    mismatch = True
                    break
            if needed_splits != []:
                mismatch = True

            # If the transaction doesn't match what is needed, delete it.  It
            # will then be recreated below.
            if amounts[ty] == 0 or mismatch:
                print "Deleting", old
                if not dry_run:
                    old.delete()
                old = None

                # If we're updating transactions for this date, recompute Bank
                # of Bob balances as well, just to be safe
                update_bob_liabilities = True

        if old is None and amounts[ty] != 0:
            insert_transaction(date, ty, amounts[ty])
            update_bob_liabilities = True

    # Recompute positive/negative Bank of Bob balances and insert if needed
    if update_bob_liabilities:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""SELECT SUM(balance)
                          FROM (SELECT userid, SUM(xactvalue) AS balance
                                FROM transactions WHERE xacttime::date <= '%s'
                                GROUP BY userid) AS balances
                          WHERE balance > 0""", (date,))
        positive = cursor.fetchone()[0]

        cursor.execute("""SELECT -SUM(balance)
                          FROM (SELECT userid, SUM(xactvalue) AS balance
                                FROM transactions WHERE xacttime::date <= '%s'
                                GROUP BY userid) AS balances
                          WHERE balance < 0""", (date,))
        negative = cursor.fetchone()[0]

        print "Update balances summary: +%.2f -%.2f" % (positive, negative)
        # FIXME: Deletion through the database API didn't seem to work (problem
        # with date as a primary key?)
        cursor.execute("DELETE FROM finance_deposit_summary WHERE date='%s'",
                       (date,))
        d = DepositBalances(date=date, positive=positive, negative=negative)
        d.save()

    # If there were any transactions found that weren't matched at all, report
    # them
    if old_transactions:
        print "Unmatched transactions:", old_transactions

def sync_day(date):
    global bob_liabilities

    from django.db import connection
    cursor = connection.cursor()

    print date
    cursor.execute("""SELECT xactvalue, xacttype FROM transactions
                      WHERE xacttime::date = '%s'""", (date,))

    (sum_deposit, sum_donate, sum_purchase, sum_socialhour, sum_writeoff) \
        = (0, 0, 0, 0, 0)

    for (amt, desc) in cursor.fetchall():
        amt = int(round(amt * 100))
        bob_liabilities += amt
        category = desc.split()[0]
        if category in ("INIT", "TRANSFER"):
            continue
        elif category == "ADD":
            sum_deposit += amt
        elif category == "BUY":
            sum_purchase -= amt
        elif category == "DONATION":
            sum_donate -= amt
        elif category == "SOCIAL":
            sum_socialhour -= amt
        elif category == "WRITEOFF":
            sum_writeoff += amt
        else:
            raise ValueError("Unknown transaction: " + desc)

    update_day(date, {'deposit': sum_deposit,
                      'donate': sum_donate,
                      'purchase': sum_purchase,
                      'socialhour': sum_socialhour,
                      'writeoff': sum_writeoff})

def sync():
    global bob_liabilities
    bob_liabilities = 0

    from django.db import connection
    cursor = connection.cursor()

    cursor.execute("""SELECT MIN(xacttime::date), MAX(xacttime::date)
                      FROM transactions""")
    (start_date, end_date) = cursor.fetchone()

    date = start_date
    while date <= end_date:
        sync_day(date)
        date += datetime.timedelta(days=1)
