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

    class Admin:
        pass

class Transaction(models.Model):
    class Meta:
        db_table = 'finance_transactions'
        permissions = [("view_transactions", "View Chez Bob Ledger"),
                       ("edit_transactions", "Update Chez Bob Ledger")]

    date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return "%s %s" % (self.date, self.description)

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
