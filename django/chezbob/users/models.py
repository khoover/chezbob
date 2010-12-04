import datetime
from decimal import Decimal
from django.db import models

class User(models.Model):
    class Meta:
        db_table = 'users'

    id =       models.IntegerField(db_column='userid', primary_key=True)
    username = models.CharField(db_column='username')
    email =    models.CharField(db_column='email')
    nickname = models.CharField(db_column='nickname')
    balance =  models.DecimalField(db_column='balance', max_digits=12, 
                                   decimal_places=2)
    disabled =           models.BooleanField(db_column='disabled')
    password =           models.CharField(db_column='pwd')
    last_purchase_time = models.DateTimeField(db_column='last_purchase_time')
    last_deposit_time =  models.DateTimeField(db_column='last_deposit_time')
    auto_logout =        models.BooleanField(db_column='pref_auto_logout')
    speech =             models.BooleanField(db_column='pref_speech')
    forget_which_product = models.BooleanField(
                               db_column='pref_forget_which_product')
    skip_purchase_confirmation = models.BooleanField(
                               db_column='pref_skip_purchase_confirm')

    def __unicode__(self):
        return "<User:" + self.username + ">"


class UserBarcode(models.Model):
    class Meta:
        db_table = 'userbarcodes'

    user = models.ForeignKey(User, db_column='userid', related_name='barcodes')
    barcode = models.CharField(db_column='barcode')

    def __unicode__(self):
        return "<Barcode:" + self.barcode + ">";
   

