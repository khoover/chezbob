from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Chez Bob products, pricing, and inventory
    (r'^products/$', 'chezbob.bobdb.views.products'),
    (r'^products/([0-9]+)/$', 'chezbob.bobdb.views.product_detail'),
    #(r'^orders/([0-9]+)/$', 'chezbob.bobdb.views.view_order'),
    #(r'^orders/([0-9]+)/update/$', 'chezbob.bobdb.views.update_order'),
    (r'^orders/$', 'chezbob.orders.views.order_list'),
    (r'^orders/(\d+)/$', 'chezbob.orders.views.order_summary'),
    (r'^orders/new/$', 'chezbob.orders.views.new_order'),
    (r'^sales/$', 'chezbob.bobdb.views.inventory'),
    (r'^sales/([0-9]+)/$', 'chezbob.bobdb.views.inventory_detail'),

    (r'^inventory/$', 'chezbob.bobdb.views.list_inventories'),
    (r'^inventory/(\d{4}-\d{1,2}-\d{1,2})/$', 'chezbob.bobdb.views.take_inventory'),
    (r'^inventory/(\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2})/$', 'chezbob.bobdb.views.take_inventory'),
    (r'^inventory/order/$', 'chezbob.bobdb.views.estimate_order'),
    (r'^inventory/order/print/$', 'chezbob.bobdb.views.display_order'),

    # Accounting
    (r'^$', 'chezbob.finance.views.redirect'),
    (r'^finance[/]$', 'chezbob.finance.views.redirect'),
    (r'^finance/accounts/$', 'chezbob.finance.views.account_list'),
    (r'^finance/ledger/$', 'chezbob.finance.views.ledger'),
    (r'^finance/account/(\d+)/$', 'chezbob.finance.views.ledger'),
    (r'^finance/transaction/(\d+)/$', 'chezbob.finance.views.edit_transaction'),
    (r'^finance/transaction/new/$', 'chezbob.finance.views.edit_transaction'),
    (r'^finance/dump/$', 'chezbob.finance.views.gnuplot_dump'),
    (r'^finance/xactdump/$', 'chezbob.finance.views.transaction_dump'),

    # User Management
    (r'^users/$', 'chezbob.users.views.user_list'),
    (r'^user/(\w+)/$', 'chezbob.users.views.user_details'),
    (r'^username/(\w+)/$', 'chezbob.users.views.user_details_byname'),

    # Cashout
    (r'^cashout/', include('chezbob.cashout.urls')),

    # Specialized database queries
    (r'^query/$', 'chezbob.query.views.home'),
    (r'^query/results/(\w+)/$', 'chezbob.query.views.results'),
    (r'^query/raw/(\w+)/$', 'chezbob.query.views.raw_table'),

    # Default admin interface for editing database
    (r'^django/', admin.site.urls),

    (r'^accounts/login/$', 'django.contrib.auth.views.login'),

    # Uncomment when running on local testing server, set correct path for js files
    # (r'^js/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/nbales/Sources/chezbob.hg/www/js/'}),
)

