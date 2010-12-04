from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.core import serializers 
import simplejson as json

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test

from chezbob.bobdb.models import BulkItem

# FROM http://djangosnippets.org/snippets/1639/
class JsonResponse(HttpResponse):
	error = ""
	__data = []
	
	def __set_data(self, data):
		self.__data = (isinstance(data, QuerySet) or hasattr(data[0], '_meta'))\
		 	and serializers.serialize('python', data) or data
	
	data = property(fset = __set_data)

	def __get_container(self):
		return json.dumps( 
			{
				"data": self.__data, 
				"error":self.error,
			}, cls = DjangoJSONEncoder)
			
	def __set_container(self, val):
		pass
	
	_container = property(__get_container, __set_container)
	
	def __init__(self, *args, **kwargs):
		kwargs["mimetype"] = "application/javascript"

		if "data" in kwargs:
			self.data = kwargs.pop("data")
			
		if "error" in kwargs:
			self.error = kwargs.pop("error")
		
		super(JsonResponse, self).__init__(*args, **kwargs)

@login_required
def bulk_items_json(request):
  products = BulkItem.objects.order_by('description')
  return JsonResponse(data=products)

#@login_required
#def update_bulk_price(request):
#  bulkid = request.POST['type_code.' + n]
  
