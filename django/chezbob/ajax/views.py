from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.core import serializers 
import simplejson as json

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test

from chezbob.bobdb.models import BulkItem
from chezbob.shortcuts import render_json

@login_required
def bulk_items_json(request):
  products = BulkItem.objects.order_by('description')
  return render_json(products)

#@login_required
#def update_bulk_price(request):
#  bulkid = request.POST['type_code.' + n]
  
