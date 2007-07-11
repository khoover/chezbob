from django.shortcuts import render_to_response
from chezbob.bobdb.models import Product

def products(request):
    return render_to_response('base.html', {'products': Product.objects.all()})
