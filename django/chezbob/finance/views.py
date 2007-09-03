import datetime
from time import strptime

from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from chezbob.finance.models import Account, Transaction, Split

view_perm_required = \
    user_passes_test(lambda u: u.has_perm('finance.view_transactions'))
edit_perm_required = \
    user_passes_test(lambda u: u.has_perm('finance.edit_transactions'))

def parse_date(datestr):
    """Parse a string representation of a date into a datetime.Date object.

    At the moment this only supports ISO-style dates (2007-01-31).  In the
    future it might be extended to other formats, and auto-detect.
    """

    return datetime.date(*strptime(datestr, "%Y-%m-%d")[0:3])

@view_perm_required
def account_list(request):
    accounts = Account.objects.all().order_by('name')
    balances = {}

    for s in Split.objects.all():
        id = s.account.id;
        if not balances.has_key(id): balances[id] = 0.0
        balances[id] += s.amount

    for a in accounts:
        a.balance = balances.get(a.id, 0.0)
        if a.is_reversed(): a.balance = -a.balance
        a.balance = round(a.balance, 2)

    return render_to_response('finance/accounts.html',
                              {'accounts': accounts})

@view_perm_required
def ledger(request, account=None):
    if account:
        account = Account.objects.get(id=account)
        title = account.name
    else:
        title = "General Ledger"

    transactions = []
    balance = 0
    for t in Transaction.objects.all().order_by('date', 'id'):
        splits = []
        include = False
        for s in t.split_set.all().order_by('-amount'):
            split = {'memo': s.memo,
                     'account': s.account,
                     'debit': "",
                     'credit': ""}
            if s.amount >= 0:
                split['debit'] = s.amount
            else:
                split['credit'] = -s.amount
            splits.append(split)
            if account is not None and s.account.id == account.id:
                include = True
                balance += s.amount
        if account is None:
            transactions.append({'info': t, 'splits': splits})
        elif include:
            transactions.append({'info': t, 'splits': splits, 'balance': balance})

    if account and account.is_reversed():
        for t in transactions:
            t['balance'] *= -1

    return render_to_response('finance/transactions.html', {'title': title, 'transactions': transactions})

@edit_perm_required
def edit_transaction(request, transaction=None):
    load_from_database = True

    if transaction == None:
        transaction = Transaction(date=datetime.date.today(),
                                  auto_generated=False)
        load_from_database = False
    else:
        transaction = get_object_or_404(Transaction, id=int(transaction))
    splits = []

    commit = True               # Is it safe to commit this transaction?

    # If the user clicked the "Update" button, don't commit yet.
    if request.POST.has_key("_update"):
        commit = False

    # If POST data was submitted, we're in the middle of editing a transaction.
    # Pull the transaction data out of the POST data.  Otherwise, we need to
    # load the initial data from the database.
    try:
        transaction.date = parse_date(request.POST['date'])
        transaction.description = request.POST['desc']
        transaction.auto_generated = request.POST.has_key('auto_generated')

        n = 0
        while True:
            n = str(int(n) + 1)
            note = request.POST['note.' + n]
            account = request.POST['account.' + n]
            if account == "":
                account = None
            else:
                account = Account.objects.get(id=int(account))

            amount = 0.0
            if request.POST['debit.' + n] != "":
                amount += float(request.POST['debit.' + n])
            if request.POST['credit.' + n] != "":
                amount -= float(request.POST['credit.' + n])
            amount = round(amount, 2)

            load_from_database = False

            if account:
                splits.append({'memo': note,
                               'account': account,
                               'amount': amount})
    except KeyError:
        # Assume we hit the end of the inputs
        pass

    if len(splits) == 0:
        commit = False

    # Load initial splits from the database, if needed
    if load_from_database:
        for s in transaction.split_set.all().order_by('-amount'):
            splits.append({'id': s.id,
                           'memo': s.memo,
                           'account': s.account,
                           'amount': s.amount})
        commit = False

    # Check if the transaction is balanced.  If not, add a balancing split to
    # be filled in by the user.
    total = 0.0
    for s in splits: total += s['amount']
    total = round(total, 2)
    if total != 0.0:
        splits.append({'memo': "", 'account': None, 'amount': -total})
        commit = False

    # Has the transaction been fully filled-in, with no problems found?  If so,
    # commit to the database.
    if commit:
        transaction.save()
        Split.objects.filter(transaction=transaction).delete()
        for s in splits:
            split = Split(transaction=transaction,
                          account=s['account'],
                          memo=s['memo'],
                          amount=s['amount'])
            split.save()
        return HttpResponseRedirect("/finance/ledger/#t%d" % (transaction.id,))

    # Include a few blank splits at the end of the transaction for entering
    # additional data.
    for i in range(2):
        splits.append({'memo': "", 'account': None, 'amount': 0.00})

    # Convert splits to a separated debit/credit format
    for s in splits:
        s['debit'] = 0.0
        s['credit'] = 0.0
        if s['amount'] > 0: s['debit'] = s['amount']
        if s['amount'] < 0: s['credit'] = -s['amount']

    return render_to_response('finance/transaction_update.html',
                              {'user': request.user,
                               'accounts': Account.objects.order_by('name'),
                               'transaction': transaction,
                               'splits': splits})
