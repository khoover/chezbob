from datetime import datetime

from django import forms

from chezbob.bobdb.models import Product
from chezbob.finance.models import Account
from chezbob.users.models import User


class UserTransactionForm(forms.Form):
  time       = forms.DateTimeField(initial=datetime.now)

class BuyForm(UserTransactionForm):
  barcode    = forms.ModelChoiceField(
                   queryset=Product.objects.all().order_by("name"))
  value      = forms.DecimalField()

  def set_transaction_fields(self, transaction, messages):
    if self.is_valid():
      transaction.time  = self.cleaned_data['time']
      transaction.barcode = self.cleaned_data['barcode']
      if self.cleaned_data['value'] is not None:
        transaction.value = self.cleaned_data['value']
      else:
        transaction.value = transaction.barcode.price
      transaction.source = "django"
      transaction.type = "BUY " + transaction.barcode.name.upper()
    else:
      messages.errors.extend(self.errors)
    
  def set_form_fields(transaction):
    return BuyForm({ 'time': transaction.xacttime,
                     'value': transaction.value,
                     'barcode': transaction.barcode, })
    
  
class TransferForm(UserTransactionForm):
  ammount    = forms.DecimalField()
  direction  = forms.ChoiceField(choices=[('to','to'),('from','from')],
                                 required=True)
  other_user = forms.ModelChoiceField(
                   queryset=User.objects.all().order_by("username"), 
                   required=True)

  def new_transaction(self, user, messages):
    message.add_error("new_transaction not implemented for trans-type transfer")

  def update_transaction(self, user, transaction, messages):
    message.add_error("update_transaction now implemented for trans-type transfer")
    
  def populate(transaction):
    raise Exception() #not implemented
                  
class AddUncountedForm(UserTransactionForm):
  ammount    = forms.DecimalField()
  repository = forms.ChoiceField(choices=[('cashbox','cashbox'),('soda','soda'),],
                                 required=True)

  def new_transaction(self, user, messages):
    message.add_error("new_transaction not implemented for trans-type add uncounted")

  def update_transaction(self, user, transaction, messages):
    message.add_error("update_transaction now implemented for trans-type add uncounted")

  def populate(transaction):
    raise Exception() #not implemented

class ReimburseForm(forms.Form):
  ammount    = forms.DecimalField()
  account    = forms.ModelChoiceField(queryset=Account.objects.all().order_by("name"),
                                      required=True)

  def new_transaction(self, user, messages):
    message.add_error("new_transaction not implemented for trans-type payment")

  def update_transaction(self, user, transaction, messages):
    message.add_error("update_transaction now implemented for trans-type payment")

  def populate(transaction):
    raise Exception() #not implemented

class RefundForm(forms.Form):
  ammount    = forms.DecimalField()

  def new_transaction(self, user, messages):
    message.add_error("new_transaction not implemented for trans-type reimbursement")

  def update_transaction(self, user, transaction, messages):
    message.add_error("update_transaction now implemented for trans-type reimbursement")

  def populate(transaction):
    raise Exception() #not implemented

class DonateForm(forms.Form):
  ammount    = forms.DecimalField()

  def new_transaction(self, user, messages):
    message.add_error("new_transaction not implemented for trans-type donation")

  def update_transaction(self, user, transaction, messages):
    message.add_error("update_transaction now implemented for trans-type donation")

  def populate(transaction):
    raise Exception() #not implemented
    
class WriteOffForm(forms.Form):
  ammount    = forms.DecimalField()

  def new_transaction(self, user, messages):
    message.add_error("new_transaction not implemented for trans-type donation")

  def update_transaction(self, user, transaction, messages):
    message.add_error("update_transaction now implemented for trans-type donation")

  def populate(transaction):
    raise Exception() #not implemented

