import datetime
from time import strptime

from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from chezbob.finance.models import Account, Transaction, Split, DepositBalances

view_perm_required = \
    user_passes_test(lambda u: u.has_perm('finance.view_transactions'))
edit_perm_required = \
    user_passes_test(lambda u: u.has_perm('finance.edit_transactions'))

def round2(amt):
    """Round an amount to two digits after the decimal place."""

    return round(amt, 2)

def parse_date(datestr):
    """Parse a string representation of a date into a datetime.Date object.

    At the moment this only supports ISO-style dates (2007-01-31).  In the
    future it might be extended to other formats, and auto-detect.
    """

    return datetime.date(*strptime(datestr, "%Y-%m-%d")[0:3])

@view_perm_required
def account_list(request):
    accounts = []
    totals = {}
    for (a, b) in Account.get_balances():
        if a.is_reversed():
            b = -b
        a.balance = round2(b)
        accounts.append(a)

        ty = Account.TYPES[a.type]
        totals[ty] = round2(totals.get(ty, 0.0) + b)

    total_list = totals.items()
    total_list.sort()
    return render_to_response('finance/accounts.html',
                              {'accounts': accounts,
                               'totals': total_list})

@view_perm_required
def ledger(request, account=None):
    if account:
        account = Account.objects.get(id=account)
        title = account.name
    else:
        title = "General Ledger"

    transactions = []
    balance = 0

    include_auto = True
    if account is None and not request.GET.has_key('all'):
        include_auto = False

    for (t, splits) in Transaction.fetch_all(account=account,
                                             include_auto=include_auto):
        split_list = []
        for s in splits:
            split = {'memo': s.memo,
                     'account': s.account,
                     'debit': "",
                     'credit': ""}
            if s.amount >= 0:
                split['debit'] = s.amount
            else:
                split['credit'] = -s.amount
            split_list.append(split)
            if account is not None and s.account.id == account.id:
                balance += s.amount
        if account is None:
            transactions.append({'info': t, 'splits': split_list})
        else:
            transactions.append({'info': t, 'splits': split_list,
                                 'balance': balance})

    if account:
        for t in transactions:
            if account.is_reversed():
                t['balance'] *= -1
            t['balance'] = round2(t['balance'])

    return render_to_response('finance/transactions.html', {'title': title, 'transactions': transactions, 'balances': account is not None})

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
            amount = round2(amount)

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
    total = round2(total)
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
        if transaction.auto_generated:
            url = "/finance/ledger/?all#t%d" % (transaction.id,)
        else:
            url = "/finance/ledger/#t%d" % (transaction.id,)
        return HttpResponseRedirect(url)

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

@view_perm_required
def gnuplot_dump(request):
    response = HttpResponse(mimetype="text/plain")

    columns = {}

    response.write("# Chez Bob Account Balances Dump\n#\n")
    response.write("# 1: Date\n")
    i = 0
    response.write("#\n# Accounts:\n")
    for a in Account.objects.order_by('name'):
        response.write("# %d: %s\n" % (i + 2, a))
        columns[a.id] = i
        i += 1
    response.write("#\n# Additional Data:\n")
    for t in sorted(Account.TYPES.keys()):
        response.write("# %d: %s Total\n" % (i + 2, Account.TYPES[t]))
        i += 1
    response.write("# %d: %s\n" % (i + 2, "Bank of Bob Accounts: Positive"))
    response.write("# %d: %s\n" % (i + 3, "Bank of Bob Accounts: Negative"))

    balances = [0.0] * len(columns)
    date = None
    multiplier = [1] * len(columns)

    totals = {}
    for t in Account.TYPES:
        totals[t] = 0.0

    for (id, i) in columns.items():
        if Account.objects.get(id=id).is_reversed():
            multiplier[i] = -1

    def dump_row():
        response.write(str(date) + "\t")

        # Accounts
        for i in range(len(balances)):
            balances[i] = round2(balances[i])
        response.write("\t".join(["%.2f" % (b,) for b in balances]))

        # Totals
        for t in sorted(Account.TYPES.keys()):
            response.write("\t%.2f" % (totals[t],))

        # Positive/negative BoB balances
        try:
            d = DepositBalances.objects.get(date=date)
            response.write("\t%.2f\t%.2f" % (d.positive, d.negative))
        except DepositBalances.DoesNotExist:
            pass
        response.write("\n")

    for t in Transaction.objects.order_by('date'):
        if t.date != date:
            if date != None:
                dump_row()
            date = t.date
        for s in t.split_set.all():
            i = columns[s.account.id]
            balances[i] += s.amount * multiplier[i]
            totals[s.account.type] += s.amount * multiplier[i]
    dump_row()

    return response

@view_perm_required
def transaction_dump(request):
    response = HttpResponse(mimetype="text/plain")

    for (t, splits) in Transaction.fetch_all(include_auto=True):
        if t.auto_generated:
            auto_str = "<auto> "
        else:
            auto_str = ""
        response.write("%s  %s%s\n" % (t.date, auto_str, t.description))
        for s in splits:
            response.write("    %10.2f [%s]" % (s.amount, s.account.name))
            if s.memo:
                response.write("  %s" % (s.memo,))
            response.write("\n")
        response.write("\n")

    return response
