import base64, datetime, math
from decimal import Decimal
from time import strptime
from django import forms

from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect
from chezbob.users.models import User, Barcode, Transaction

class MakePurchaseForm(forms.Form):
  time    = forms.DateTimeField()
  value   = forms.DecimalField()
  barcode = forms.ModelChoiceField(
      queryset=Product.objects.all().order_by("name"), 
      empty_label="(None)")

@login_required
def user_list(request):
    users = list(User.objects.all())
    return render_to_response('users/user_list.html',
                              {'user': request.user,
                               'title': "Users Overview",
                               'users': users})

@login_required
def user_details(request, username):
    users = list(User.objects.filter(username=username))
    user, barcodes, transactions, title = None, None, None, None
    
    errors = []
    if len(users) < 1:
      errors.append("Error: User %s not found!" % username)
    elif len(users) > 1:
      errors.append("Error: Multiple users %s found!" & username)
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


