import base64, datetime, math
from decimal import Decimal
from time import strptime

from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import connection, transaction

from chezbob.users.models import User, Barcode, Transaction
from chezbob.users.forms import *
from chezbob.shortcuts import BobMessages, render_bob_messages, render_or_error, redirect_or_error


@login_required
def user_list(request):
  users = list(User.objects.all().order_by("name"))
  return render_to_response('users/user_list.html',
                            {'user': request.user,
                             'title': "Users Overview",
                             'users': users})
                               
@login_required
def user_details_byname(request, username):
  """ Provides a convenience URL to access user details pages by username
      rather than by userid.  The username is not the primary means of 
      identifying users because it complications the function of changing a 
      username from the userdetails page.  Also, many times it is more 
      convenient to look up a user by id.
  """
  users = list(User.objects.filter(username=username))
    
  messages = BobMessages()
  if len(users) < 1:
    messages.add_error("Error: User %s not found!" % username)
  elif len(users) > 1:
    messages.add_error("Error: Multiple users %s found!" & username)
  else:
    return redirect_or_error(
        reverse('chezbob.users.views.user_details', args=[users[0].id]),
        messages)

  return render_or_error('users/user_details.html', messages)                               

@transaction.commit_manually
def new_transaction(type, bound, user, messages):
  try:
    if not bound.is_valid:
      messages.errors(bound.error)
      return
    tran = Transaction()
    tran.user = user
    bound.set_transaction_fields(tran, messages)
    if messages.has_errors():
      return
    user.balance = F('balance') - tran.value
    if type == 'ADD', 'REFUND', 'DONATION', 'WRITEOFF': pass
    elif type == 'BUY':
      cursor = connection.cursor()
      cursor.execute("""INSERT INTO aggregate_purchases 
                        (date, barcode, quantity, price, bulkid) 
                        VALUES (%s, '%s', %s, %s, %s)""",
                     (tran.time.date,
                      tran.barcode.barcode, 1,
                      tran.value,
                      tran.barcode.bulkid))
    elif type == 'TRANSFER':
      messages.error("Add new transfer transaction not supported yet")
    elif type == 'REIMBURSE':
      messages.error("Add new reimburse transaction not supported yet")
    else:
      messages.error("Unknown transaction category %s. Cannot add transaction" 
                     % [type])
    if not messages.has_errors():
      tran.save()
      user.save()
    messages.note("New transaction generated %s" % unicode(transaction))
  except Exception as e:
    transaction.rollback()
    messages.error("Exception while creating new transaction: " + e.message)
  else:
    transaction.commit()
    
@transaction.commit_manually  
def edit_transaction(bound, tran, messages):
  try:
    if not bound.is_valid:
      messages.errors(bound.error)
      return
  except Exception as e:
    transaction.rollback()
    messages.error("Exception while creating new transaction: " + e.message)
  else:
    transaction.commit()
  

@login_required
def user_details(request, userid):
  users = list(User.objects.filter(id=userid))
  user, barcodes, transactions, title = None, None, None, None

  messages = BobMessages()
  if len(users) < 1:
    messages.add_error("Error: Userid %s not found." % userid)
  elif len(users) > 1:
    messages.add_error("Error: Multiple users with id %s found." & userid)
  else:
    user = users[0]
    barcodes = Barcode.objects.filter(user=user.id)
    transactions = Transaction.objects.filter(user=user.id).order_by('time')
  
  def make_form(type, title, form):
    form_types[type] = {'title' : title,
                        'type'  : type,
                        'form'  : form,
                        'fields': form(),
                        'show'  : type + "_open" in request.POST }
  form_types = {}  
  make_form('BUY',       'Make Buy Transaction', BuyForm)
  make_form('TRANSFER',  'Make Transfer',        TransferForm)
  make_form('ADD',       'Add Cash',             AddUncountedForm)
  make_form('REIMBURSE', 'Issue Reimbursement',  ReimburseForm)
  make_form('REFUND',    'Issue Refund',         RefundForm)
  make_form('DONATION',  'Donate Balance',       DonateForm)
  make_form('WRITEOFF',  'Write-off Balance',    WriteOffForm)
  
  for type in form_types:
    if type + "_save" in request.POST:
      bound = form_types[type]['form'](request.POST)
      new_transaction(type, bound, user, messages)
      
  for tran in transactions:
    if "delete_tran_" + tran.id in request.POST:
      type = tran.type()
      delete_transaction(tran, messages)
    if "edit_tran_" + tran.id in request.POST:
      type = tran.type()
      bound = form_types[type]['form'](request.POST)
      edit_transaction(bound, tran, messages)
      if messages.has_errors():
        # it is possible there is a partially changed but aborted trans
        # refresh QuerySet to avoid this possibility
        transactions = Transaction.objects.filter(user=user.id).order_by('time')

  messages['tools'] = form_types.values()

  return render_or_error('users/user_details.html', 
                          messages.extend({ 'user'          : request.user,
                                            'title'         : title,
                                            'user_detailed' : user,
                                            'barcodes'      : barcodes,
                                            'transactions'  : transactions}))

