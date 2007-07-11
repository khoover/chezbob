from django.shortcuts import render_to_response
from chezbob.bobdb.models import Product

def products(request):
    return render_to_response('base.html',
                              {'user': request.user,
                               'products': Product.objects.all()})
