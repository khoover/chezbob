import base64, datetime, math
from decimal import Decimal
from time import strptime

from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from chezbob.users.models import User, Barcode, Transaction


@login_required
def user_list(request):
    users = list(User.objects.all())
    return render_to_response('users/user_list.html',
                              {'user': request.user,
                               'title': "Users Overview",
                               'users': users})

@login_required
def user_details(request, userid):
    users = list(User.objects.filter(id=userid))
    user, barcodes, transactions, title = None, None, None, None
    
    errors = []
    if len(users) < 1:
      errors.append("Error: User %s not found!" % userid)
    elif len(users) > 1:
      errors.append("Error: Multiple users %s found!" & userid)
    else:
		  user = users[0]
		  barcodes = Barcode.objects.filter(user=user.id)
		  transactions = Transaction.objects.filter(user=user.id).order_by('time')

    return render_to_response('users/user_details.html',
                              {'errors': errors,
                               'user': request.user,
                               'title': title,
                               'user_detailed': user,
                               'barcodes' : barcodes,
                               'transactions' : transactions,})
