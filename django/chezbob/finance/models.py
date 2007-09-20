from django.db import models

class Account(models.Model):
    class Meta:
        db_table = 'finance_accounts'

    ASSET = 'A'
    EQUITY = 'Q'
    EXPENSE = 'E'
    INCOME = 'I'
    LIABILITY = 'L'

    TYPES = {
        ASSET: "Asset",
        EQUITY: "Equity",
        EXPENSE: "Expense",
        INCOME: "Income",
        LIABILITY: "Liability",
    }

    type = models.CharField(maxlength=1, choices=TYPES.items())
    name = models.CharField(maxlength=256)

    def __str__(self):
        return "%s [%s]" % (self.name, self.TYPES[self.type])

    def is_reversed(self):
        return self.type in ('Q', 'I', 'L')

    @classmethod
    def get_balances(cls):
        """Return a list of all accounts, and their current balances."""

        from django.db import connection
        cursor = connection.cursor()

        balances = {}
        cursor.execute("""SELECT account_id, sum(amount)
                          FROM finance_splits GROUP BY account_id""")
        for (id, balance) in cursor.fetchall():
            balances[id] = balance

        result = []
        for a in Account.objects.order_by('name'):
            result.append((a, balances.get(a.id, 0.0)))

        return result

    class Admin:
        ordering = ['name']

class Transaction(models.Model):
    class Meta:
        db_table = 'finance_transactions'
        permissions = [("view_transactions", "View Chez Bob Ledger"),
                       ("edit_transactions", "Update Chez Bob Ledger")]

    date = models.DateField()
    description = models.TextField()
    auto_generated = models.BooleanField()

    def __str__(self):
        return "%s %s" % (self.date, self.description)

    @classmethod
    def fetch_all(cls, account=None, include_auto=True):
        """Return a list of all transactions and splits in the database.

        The result is a sequence of tuples: (transaction, [split list]).
        Transactions are sorted by date.
        """

        from django.db import connection
        cursor = connection.cursor()

        accounts = {}
        for a in Account.objects.all():
            accounts[a.id] = a

        result = []
        extra_conditions = ""
        extra_arguments = []

        if not include_auto:
            extra_conditions += "AND NOT finance_transactions.auto_generated "
        if account is not None:
            extra_conditions += "AND finance_transactions.id IN (SELECT transaction_id FROM finance_splits WHERE account_id = %s) "
            extra_arguments.append(account.id)
        query = """SELECT finance_transactions.id,
                          finance_transactions.date,
                          finance_transactions.description,
                          finance_transactions.auto_generated,
                          finance_splits.id,
                          finance_splits.account_id,
                          finance_splits.amount,
                          finance_splits.memo
                   FROM finance_transactions, finance_splits
                   WHERE finance_splits.transaction_id = finance_transactions.id
                         %s
                   ORDER BY finance_transactions.date,
                            finance_transactions.id""" % (extra_conditions,)
        cursor.execute(query, extra_arguments)

        transaction = None
        for (id, date, desc, auto, split_id, acct, amt, memo) in cursor.fetchall():
            if transaction is None or transaction[0].id != id:
                if transaction is not None:
                    result.append(transaction)
                transaction = (Transaction(id=id, date=date, description=desc,
                                           auto_generated=auto),
                               [])
            transaction[1].append(Split(id=split_id,
                                        transaction=transaction[0],
                                        account=accounts[acct],
                                        amount=amt, memo=memo))

            # FIXME: This is to prevent a lookup of split.account for having to
            # go back to the database later, which is expensive.  But it messes
            # with Django internals.  There must be a cleaner way to accomplish
            # this.
            transaction[1][-1]._account_cache = accounts[acct]

        if transaction is not None:
            result.append(transaction)

        for (t, splits) in result:
            splits.sort(key=lambda s: -s.amount)
        return result

    class Admin:
        pass

class Split(models.Model):
    class Meta:
        db_table = 'finance_splits'

    transaction = models.ForeignKey(Transaction)
    account = models.ForeignKey(Account)
    amount = models.FloatField(max_digits=12, decimal_places=2)
    memo = models.CharField(maxlength=256, blank=True)

    def __str__(self):
        return "%.2f %s" % (self.amount, self.account)

    class Admin:
        pass
