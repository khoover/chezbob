from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from chezbob.bobdb.models import Product

def products(request):
    products = list(Product.objects.all())

    for p in products:
        try:
            p.markup_amt = p.price - p.bulk.unit_price()
            p.markup_pct = ((p.price / p.bulk.unit_price()) - 1.0) * 100
        except ObjectDoesNotExist:
            pass

    def sort_field(p):
        try:
            key = int(request.GET.get("o", 0))
            if key == 0:
                return p.name
            elif key == 1:
                return p.price
            elif key == 2:
                return p.bulk.unit_price()
            elif key == 3:
                return p.markup_amt
            elif key == 4:
                return p.markup_pct
        except:
            return None
    products.sort(lambda x, y: cmp(sort_field(x), sort_field(y)))

    return render_to_response('chezbob/base.html',
                              {'user': request.user,
                               'title': "Products Overview",
                               'products': products})
