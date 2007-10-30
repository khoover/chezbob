import datetime
import time
#from time import strptime
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf.urls.defaults import *
from django.http import HttpResponse, HttpResponseRedirect
from chezbob.cashout.models import CashOut, Entity, CashCount

view_perm_required = \
        user_passes_test(lambda u: u.has_perm('cashcount.view_transactions'))
edit_perm_required = \
        user_passes_test(lambda u: u.has_perm('cashcount.edit_transactions'))

time_format = "%Y-%m-%d %H:%M"

def parse_datetime(datetimestr):
    return time.strftime(time_format,(time.strptime(datetimestr, time_format)))

@view_perm_required
def ledger(request):
    title = 'Moo'

    cashouts = []

    for (c, cashcounts) in CashOut.fetch_all():
        cashcount_list = [];

        total = 0;
        for s in cashcounts:
            cashcount = {'memo': s.memo,
                         'entity': s.entity,
                         'total': s.total}
            total += s.total

            cashcount_list.append(cashcount)

        cashouts.append({
                         'info': c, 
                         'counts': cashcount_list,
                         'total':total
                         })

    return render_to_response('cashout/cashouts.html',
                              {'title': title,
                               'cashouts': cashouts
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

            try:
                bill100 = int(request.POST['bill100.' + n])
            except ValueError: bill100 = 0
            try:
                bill50  = int(request.POST['bill50.' + n])
            except ValueError: bill50 = 0
            try:
                bill20  = int(request.POST['bill20.' + n])
            except ValueError: bill20 = 0 
            try:
                bill10  = int(request.POST['bill10.' + n])
            except ValueError: bill10 = 0 
            try:
                bill5   = int(request.POST['bill5.' + n])
            except ValueError: bill5  = 0 
            try:
                bill1   = int(request.POST['bill1.' + n])
            except ValueError: bill1  = 0 
            try:
                coin100 = int(request.POST['coin100.' + n])
            except ValueError: coin100 = 0
            try:
                coin50  = int(request.POST['coin50.' + n])
            except ValueError: coin50 = 0 
            try:
                coin25  = int(request.POST['coin25.' + n])
            except ValueError: coin25 = 0 
            try:
                coin10  = int(request.POST['coin10.' + n])
            except ValueError: coin10 = 0 
            try:
                coin5   = int(request.POST['coin5.' + n])
            except ValueError: coin5  = 0 
            try:
                coin1   = int(request.POST['coin1.' + n])
            except ValueError: coin1  = 0 
            try:
                other   = float(request.POST['other.' + n])
            except ValueError: other  = 0 

            total =  \
                      bill100 * 100 +\
                      bill50 * 50 +\
                      bill20 * 20 +\
                      bill10 * 10 +\
                      bill5 * 5 +\
                      bill1 +\
                      coin100 +\
                      coin50 * 0.50 +\
                      coin25 * 0.25 +\
                      coin10 * 0.10 +\
                      coin5 * 0.05 +\
                      coin1 * 0.01 +\
                      other
                      
                    

            if entity == "":
                entity = None
            else:
                entity = Entity.objects.get(id=int(entity))

            load_from_database = False

            if entity:
                counts.append({
                                'memo' : memo,
                                'entity' : entity,
                                'bill100': bill100,
                                'bill50': bill50,
                                'bill20': bill20,
                                'bill10': bill10,
                                'bill5': bill5,
                                'bill1': bill1,
                                'coin100': coin100,
                                'coin50': coin50,
                                'coin25': coin25,
                                'coin10': coin10,
                                'coin5': coin5,
                                'coin1': coin1,
                                'other': other,
                                'total': total
                              })
    except KeyError:
        # Assume we hit the end of the inputs
        pass

    if len(counts) == 0:
        commit = False

    if load_from_database:
        for c in cashout.cashcount_set.all().order_by('entity'):
            counts.append({
                            'id': c.id,
                            'memo': c.memo,
                            'entity': c.entity,
                            'bill100': c.bill100,
                            'bill50': c.bill50,
                            'bill20': c.bill20,
                            'bill10': c.bill10,
                            'bill5': c.bill5,
                            'bill1': c.bill1,
                            'coin100': c.coin100,
                            'coin50': c.coin50,
                            'coin25': c.coin25,
                            'coin10': c.coin10,
                            'coin5': c.coin5,
                            'coin1': c.coin1,
                            'other': c.other,
                            'total': c.total
                           })
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

    # Include blank entities?
    entitys = Entity.objects.order_by('name')
    for e in entitys:
        if not e in map(lambda s:s['entity'], counts):
            counts.append({'memo': "", 'entity': e})

    for i in range(1):
        counts.append({'memo': ""})

    return render_to_response('cashout/cashout_update.html',
                              {
                               'user': request.user,
                               'entitys': entitys,
                               'cashout': cashout,
                               'cashcounts': counts
                              }
                              )
