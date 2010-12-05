from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Chez Bob products, pricing, and inventory
    (r'^admin/products/$', 'chezbob.bobdb.views.products'),
    (r'^admin/products/([0-9]+)/$', 'chezbob.bobdb.views.product_detail'),
    (r'^admin/orders/([0-9]+)/$', 'chezbob.bobdb.views.view_order'),
    (r'^admin/orders/([0-9]+)/update/$', 'chezbob.bobdb.views.update_order'),
    (r'^admin/sales/$', 'chezbob.bobdb.views.inventory'),
    (r'^admin/sales/([0-9]+)/$', 'chezbob.bobdb.views.inventory_detail'),

    (r'^admin/inventory/$', 'chezbob.bobdb.views.list_inventories'),
    (r'^admin/inventory/(\d{4}-\d{1,2}-\d{1,2})/$', 'chezbob.bobdb.views.take_inventory'),
    (r'^admin/inventory/order/$', 'chezbob.bobdb.views.estimate_order'),
    (r'^admin/inventory/order/print/$', 'chezbob.bobdb.views.display_order'),

    (r'^admin/ajax/bulk_items_json/$', 'chezbob.ajax.views.bulk_items_json'),

    # Accounting
    (r'^admin/$', 'chezbob.finance.views.redirect'),
    (r'^admin/finance[/]$', 'chezbob.finance.views.redirect'),
    (r'^admin/finance/accounts/$', 'chezbob.finance.views.account_list'),
    (r'^admin/finance/ledger/$', 'chezbob.finance.views.ledger'),
    (r'^admin/finance/account/(\d+)/$', 'chezbob.finance.views.ledger'),
    (r'^admin/finance/transaction/(\d+)/$', 'chezbob.finance.views.edit_transaction'),
    (r'^admin/finance/transaction/new/$', 'chezbob.finance.views.edit_transaction'),
    (r'^admin/finance/dump/$', 'chezbob.finance.views.gnuplot_dump'),
    (r'^admin/finance/xactdump/$', 'chezbob.finance.views.transaction_dump'),

    # User Management
    (r'^admin/users/$', 'chezbob.users.views.user_list'),
    (r'^admin/user/(\w+)/$', 'chezbob.users.views.user_details'),

    # Cashout
    (r'^admin/cashout/', include('chezbob.cashout.urls')),

    # Specialized database queries
    (r'^admin/query/$', 'chezbob.query.views.home'),
    (r'^admin/query/results/(\w+)/$', 'chezbob.query.views.results'),
    (r'^admin/query/raw/(\w+)/$', 'chezbob.query.views.raw_table'),

    # Default admin interface for editing database
    (r'^admin/django/(.*)', admin.site.root),

    (r'^admin/accounts/login/$', 'django.contrib.auth.views.login'),

    # Uncomment when running on local testing server, set correct path for js files
    # (r'^js/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/nbales/Sources/chezbob.hg/www/js/'}),
)

