import datetime
import time
#from time import strptime
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf.urls.defaults import *
from django.http import HttpResponse, HttpResponseRedirect
from chezbob.cashout.models import CashOut, Entity, CashCount

import chezbob.finance.models as finance

import re

view_perm_required = \
        user_passes_test(lambda u: u.has_perm('cashout.view_cashouts'))
edit_perm_required = \
        user_passes_test(lambda u: u.has_perm('cashout.change_cashout'))

time_format = "%Y-%m-%d %H:%M"
time_format2 = "%Y-%m-%d %H:%M:%S"

def parse_datetime(datetimestr):
    try:
        return time.strftime(time_format,(time.strptime(datetimestr, time_format)))
    except ValueError:
        pass

    return time.strftime(time_format2,(time.strptime(datetimestr, time_format2)))

def datetimetodate(datetimestr):
    try:
        return time.strftime("%Y-%m-%d",(time.strptime(datetimestr, time_format)))
    except ValueError:
        pass

    return time.strftime("%Y-%m-%d",(time.strptime(datetimestr, time_format2)))


@view_perm_required
def ledger(request):
    title = 'Cashouts'

    cashouts = []

    balance = 0
    for (c, cashcounts) in CashOut.fetch_all():
        cashcount_list = [];

        total = 0;
        for s in cashcounts:
            cashcount = {'memo': s.memo,
                         'entity': s.entity,
                         'total': s.total}
            total += s.total

            cashcount_list.append(cashcount)

        balance += total
        cashouts.append({
                         'info': c, 
                         'counts': cashcount_list,
                         'total':total,
                         'balance':balance
                         })

    return render_to_response('cashout/cashouts.html',
                              {'title': title,
                               'cashouts': cashouts
                               })

@view_perm_required
def cashonhand(request):
    title = 'Cashouts'

    fields = CashCount.fields
    field_names = CashCount.field_names
    cashouts = []

    onhand_total = {};
    for f in fields:
        onhand_total[f] = 0

    m = re.compile(r'^(?:bill|coin)')

    for (c, cashcounts) in CashOut.fetch_all():
        cashcount_list = [];

        for s in cashcounts:
            cashcount = []
            for f in fields:
                try:
                    onhand_total[f] += s.__dict__[f]
                except TypeError:
                    pass # Probably 0 anyway.

                if m.search(f):
                    cashcount.append("%d" % (s.__dict__[f]))
                else:
                    cashcount.append("%.2f" % (s.__dict__[f]))

            cashcount_list.append({'count':cashcount, 
                                   'entity':s.entity})

        total = []
        for f in fields:
            total.append(onhand_total[f])

        cashouts.append({
                         'info': c, 
                         'counts': cashcount_list,
                         'total':total,
                         })

    return render_to_response('cashout/cashonhand.html',
                              {'title': title,
                               'cashouts': cashouts,
                               'fields': fields,
                               'field_names': field_names
                               })

@edit_perm_required
def edit_cashout(request, cashout=None):
    load_from_database = True

    if cashout == None:
        cashout = CashOut(datetime=time.strftime(time_format,time.localtime()))
        load_from_database = False
    else:
        cashout = get_object_or_404(CashOut, id=int(cashout))

    counts = []

    commit = True

    fields = CashCount.fields
    field_values = CashCount.field_values
    field_names = CashCount.field_names

    if request.POST.has_key("_update"):
        commit = False

    try:
        cashout.notes = request.POST['notes']
        cashout.datetime = parse_datetime(request.POST['datetime'])

        n = 0
        while True:
            n = str(int(n) + 1)
            memo = request.POST['memo.' + n]
            entity = request.POST['entity.' + n]

            values = {}

            for f in fields[:-1]:
                try:
                    if f != 'other':
                        values[f] = int(request.POST[f + '.' + n])
                    else:
                        values[f] = float(request.POST[f + '.' + n])
                except ValueError: values[f] = 0

            total = 0

            for f in fields[:-1]:
                total += values[f] * field_values[f]

            if entity == "":
                entity = None
            else:
                entity = Entity.objects.get(id=int(entity))

            load_from_database = False

            if entity and total != 0:
                count_count = []

                count = {
                         'memo' : memo,
                         'entity' : entity,
                         'total' : total
                         }

                for f in fields[:-1]:
                    count[f] = values[f]
                    count_count.append(values[f])

                count_count.append(total)
                count['count_value'] = count_count

                counts.append(count)
    except KeyError:
        # Assume we hit the end of the inputs
        pass

    if len(counts) == 0:
        commit = False

    if load_from_database:
        for c in cashout.cashcount_set.all().order_by('entity'):
            count = {
                   'id':c.id,
                   'memo':c.memo,
                   'entity':c.entity
                   }
            count_count = []
            for f in fields:
                count[f] = c.__dict__[f]
                count_count.append(count[f])

            count['count_value'] = count_count
            counts.append(count)

            commit = False

    if commit:
        cashout.save()
        CashCount.objects.filter(cashout=cashout).delete()
        for c in counts:
            count = CashCount(
                              cashout=cashout,
                              entity=c['entity'],
                              memo=c['memo'],
                              bill100=c['bill100'],
                              bill50=c['bill50'],
                              bill20=c['bill20'],
                              bill10=c['bill10'],
                              bill5=c['bill5'],
                              bill1=c['bill1'],
                              coin100=c['coin100'],
                              coin50=c['coin50'],
                              coin25=c['coin25'],
                              coin10=c['coin10'],
                              coin5=c['coin5'],
                              coin1=c['coin1'],
                              other=c['other']
                              )
            count.save()

        url = "/cashout/ledger#c%d" % (cashout.id,)

        return HttpResponseRedirect(url)

    blank_values = []
    for f in fields:
        blank_values.append("")

    # Include blank entities?
    entitys = Entity.objects.order_by('name')
    if len(counts) == 0:
        for e in entitys:
            if not e in map(lambda s:s['entity'], counts):
                counts.append({'memo': "", 
                              'entity': e,
                              'count_value':blank_values})

    for i in range(1):
        counts.append({'memo': "", 'count_value':blank_values})

    return render_to_response('cashout/cashout_update.html',
                              {
                               'user': request.user,
                               'entitys': entitys,
                               'cashout': cashout,
                               'cashcounts': counts,
                               'fields' : CashCount.fields,
                               'field_names': CashCount.field_names,
                               'field_index' : range(0,
                                                     len(CashCount.fields[:-1]))
                              }
                              )

@edit_perm_required
def gen_transaction(request, cashout):
    cashout = get_object_or_404(CashOut, id=int(cashout))
   
    transaction = finance.Transaction(date=datetimetodate(
                                                str(cashout.datetime)
                                                         ), 
                                      auto_generated=False)


    splits = []

    account_name = {
            'cash' : 7,
            'collected' : 24,
            'bank' : 1,
            'inventory' : 5
            }

    balance = 0
    for c in cashout.cashcount_set.all().order_by('entity'):
        total = c.total
        balance += total
        split = {}

        if c.entity.name in ("Soda Machine", "Cash Box"):
            transaction.description = "Cash Collected"
            split['account'] = finance.Account.objects.get(
                                        id=int(account_name['cash'])
                                                          )

            split['memo'] = c.entity.name 

        elif c.entity.name in ("To Bank"):
            split['account'] = finance.Account.objects.get(
                                        id=int(account_name['bank'])
                                                          )
            split['memo'] = ""
            transaction.description = "Cash Deposit"

        elif c.entity.name in ("Payment"):
            transaction.description = cashout.notes
            split['account'] = finance.Account.objects.get(
                                        id=int(account_name['inventory'])
                                                          )
            split['memo'] = ""


        if total < 0: split['debit'] = -total
        if total > 0: split['credit'] = total

        splits.append(split)

    s = {
          'account':
                finance.Account.objects.get(id=int(account_name['collected'])),
           'amount':balance
        }
    if balance > 0: s['debit'] = balance
    if balance < 0: s['credit'] = -balance

    splits.append(s)
                

    return render_to_response('finance/transaction_update.html',
                              {
                          'user': request.user,
                          'accounts': finance.Account.objects.order_by('name'),
                          'transaction': transaction,
                          'splits': splits,
                          'action':'/finance/transaction/new/'
                               })
    
