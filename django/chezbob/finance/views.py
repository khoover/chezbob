from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from chezbob.finance.models import Account, Transaction, Split

view_perm_required = \
    user_passes_test(lambda u: u.has_perm('finance.view_transactions'))
edit_perm_required = \
    user_passes_test(lambda u: u.has_perm('finance.edit_transactions'))

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
    return render_to_response('finance/transactions.html', {'title': title, 'transactions': transactions})

@edit_perm_required
def edit_transaction(request, transaction):
    transaction = get_object_or_404(Transaction, id=int(transaction))

    splits = []
    for s in transaction.split_set.all().order_by('-amount'):
        split = {'memo': s.memo,
                 'account': s.account,
                 'debit': "",
                 'credit': ""}
        if s.amount >= 0:
            split['debit'] = s.amount
        else:
            split['credit'] = -s.amount
        splits.append(split)
    splits.append({'memo': "", 'account': None, 'debit': "", 'credit': ""})
    splits.append({'memo': "", 'account': None, 'debit': "", 'credit': ""})

    return render_to_response('finance/transaction_update.html',
                              {'user': request.user,
                               'accounts': Account.objects.order_by('name'),
                               'transaction': transaction,
                               'splits': splits})
