from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from chezbob.bobdb.models import BulkItem, Product, Order, OrderItem, TAX_RATE

##### Product summary information #####
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

    return render_to_response('bobdb/product_list.html',
                              {'user': request.user,
                               'title': "Products Overview",
                               'products': products})

def product_detail(request, barcode):
    product = get_object_or_404(Product, barcode=barcode)

    try:
        product.markup_amt = product.price - product.bulk.unit_price()
        product.markup_pct = ((product.price / product.bulk.unit_price()) - 1.0) * 100
    except ObjectDoesNotExist:
        pass

    return render_to_response('bobdb/product_detail.html',
                              {'user': request.user,
                               'title': "Product Detail",
                               'product': product})

##### Order tracking #####
@login_required
def view_order(request, order):
    order = get_object_or_404(Order, id=int(order))
    items = order.orderitem_set.all()

    return render_to_response('bobdb/order_info.html',
                              {'user': request.user,
                               'title': "Order Summary",
                               'order': order,
                               'items': items})

@login_required
def update_order(request, order):
    order = get_object_or_404(Order, id=int(order))

    item_list = []              # Items stored in the database
    new_items = []              # New entries not yet written to database

    # If any POST data was submitted, process it, since it might include
    # updates to existing items or new items.  We can distinguish the two
    # because existing items will include an "id." field.
    try:
        n = 0
        while True:
            n = str(int(n) + 1)

            try: number = int(request.POST['number.' + n])
            except ValueError: number = 0
            if number < 0: number = 0

            # Update to existing item in the database.  If quantity has
            # been cleared, then delete this item.  Otherwise, make any
            # appropriate edits.
            order_item = None
            try:
                id = int(request.POST['id.' + n])
                order_item = OrderItem.objects.get(id=id)
            except: pass

            if order_item:
                if not number:
                    order_item.delete()
                else:
                    order_item.number = number
                    order_item.quantity \
                        = int(request.POST['quantity.' + n])
                    order_item.cost_taxable \
                        = float(request.POST['taxable.' + n])
                    order_item.cost_nontaxable \
                        = float(request.POST['nontaxable.' + n])
                    order_item.save()
                continue

            # Filling in details for an entry.  If complete, save to the
            # database.
            if request.POST.has_key('type_code.' + n):
                if not number: continue

                try:
                    bulk_code = int(request.POST['type_code.' + n])
                    bulk_type = BulkItem.objects.get(bulkid=bulk_code)
                    quantity = int(request.POST['quantity.' + n])
                    nontaxable = float(request.POST['nontaxable.' + n])
                    taxable = float(request.POST['taxable.' + n])
                    order_item = OrderItem(order=order,
                                           bulk_type=bulk_type,
                                           quantity=quantity,
                                           number=number,
                                           cost_taxable=taxable,
                                           cost_nontaxable=nontaxable)
                    order_item.save()
                except:
                    pass

                continue

            # New entry.  Perform a search based on the name for matching
            # items, and add them to new_items so the user can fill in the rest
            # of the details.
            name = request.POST['type.' + n]
            if not name: continue

            if not number: number = ""
            matches = BulkItem.objects.filter(description__icontains=name)

            # If there were no matches, re-present the query to the user.
            if len(matches) == 0:
                new_items.append({'blank': True,
                                  'type': name})

            # Force user to re-enter numbers if multiple matches occurred.
            if len(matches) > 1: number = ""

            for m in matches:
                new_items.append({'blank': False,
                                  'type': m,
                                  'number': number,
                                  'quantity': m.quantity,
                                  'nontaxable': m.cost_nontaxable(),
                                  'taxable': m.cost_taxable()})
    except KeyError:
        # Assume we hit the end of the inputs
        pass

    # Include all items listed in the database for this order.
    total_notax = 0.0
    total_tax = 0.0
    for i in order.orderitem_set.order_by('id'):
        item = {'blank': False,
                'id': i.id,
                'number': i.number,
                'quantity': i.quantity,
                'type': i.bulk_type,
                'nontaxable': i.cost_nontaxable,
                'taxable': i.cost_taxable}
        if abs(i.cost_nontaxable - i.bulk_type.cost_nontaxable()) \
                + abs(i.cost_taxable - i.bulk_type.cost_taxable()) > 0.005:
            item['message'] = "Price differs from bulk data"
        item_list.append(item)
        total_notax += i.cost_nontaxable * i.number
        total_tax += i.cost_taxable * i.number

    total = round(total_notax + total_tax * (1 + TAX_RATE), 2)

    for i in range(5):
        new_items.append({'blank': True})

    return render_to_response('bobdb/order_update.html',
                              {'user': request.user,
                               'title': "Update Order",
                               'order': order,
                               'items': item_list + new_items,
                               'total_notax': total_notax,
                               'total_tax': total_tax,
                               'total': total})
