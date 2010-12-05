import datetime
from decimal import Decimal
from django.db import models
from chezbob.bobdb import Product

class User(models.Model):
    class Meta:
        db_table = 'users'

    id =       models.IntegerField(db_column='userid', primary_key=True)
    username = models.CharField(db_column='username', max_length=255)
    email =    models.CharField(db_column='email', max_length=255)
    nickname = models.CharField(db_column='nickname', max_length=255)
    balance =  models.DecimalField(db_column='balance', max_digits=12, 
                                   decimal_places=2)
    disabled =           models.BooleanField(db_column='disabled')
    password =           models.CharField(db_column='pwd', max_length=255)
    last_purchase_time = models.DateTimeField(db_column='last_purchase_time')
    last_deposit_time =  models.DateTimeField(db_column='last_deposit_time')
    auto_logout =        models.BooleanField(db_column='pref_auto_logout')
    speech =             models.BooleanField(db_column='pref_speech')
    forget_which_product = models.BooleanField(
                               db_column='pref_forget_which_product')
    skip_purchase_confirmation = models.BooleanField(
                               db_column='pref_skip_purchase_confirm')

    def __unicode__(self):
        return "{User:" + self.username + "}"


class Barcode(models.Model):
    class Meta:
        db_table = 'userbarcodes'

    user = models.ForeignKey(User, db_column='userid', related_name='barcodes')
    barcode = models.CharField(db_column='barcode', primary_key=True, max_length=255)

    def __unicode__(self):
        return "{Barcode:" + self.barcode + "}";
        
class Transaction(models.Model):
    class Meta:
        db_table = 'transactions'
    
    time    = models.DateTimeField(db_column='xacttime')
    value   = models.DecimalField(db_column='xactvalue', max_digits=12, 
                                  decimal_places=2)
    type    = models.CharField(db_column='xacttype', max_length=255)
    source  = models.CharField(db_column='source', max_length=255)
    barcode = models.ForeignKey(Product, db_column='barcode', max_length=255, 
                                related_name='sales')
    user    = models.ForeignKey(User, db_column='userid', 
                                related_name='purchases')

    def __unicode__(self):
        return "{Transaction: $" + self.value + "@" + self.time + "}";
   

