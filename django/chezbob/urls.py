from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Default admin interface for editing database
    (r'^admin/', include('django.contrib.admin.urls')),
    #(r'^accounts/login/$', 'django.contrib.auth.views.login'),

    # Chez Bob pages
    (r'^products/$', 'chezbob.bobdb.views.products'),
    (r'^products/([0-9]+)/$', 'chezbob.bobdb.views.product_detail'),

    (r'^orders/([0-9]+)/$', 'chezbob.bobdb.views.view_order'),
    (r'^orders/([0-9]+)/update/$', 'chezbob.bobdb.views.update_order'),

    (r'^inventory/$', 'chezbob.bobdb.views.inventory'),
    (r'^inventory/([0-9]+)/$', 'chezbob.bobdb.views.inventory_detail'),

    # Accounting
    (r'^finance/accounts/$', 'chezbob.finance.views.account_list'),
    (r'^finance/ledger/$', 'chezbob.finance.views.ledger'),
    (r'^finance/account/(\d+)/$', 'chezbob.finance.views.ledger'),
    (r'^finance/transaction/(\d+)/$', 'chezbob.finance.views.edit_transaction'),
    (r'^finance/transaction/new/$', 'chezbob.finance.views.edit_transaction'),
    (r'^finance/dump/$', 'chezbob.finance.views.gnuplot_dump'),
    (r'^finance/xactdump/$', 'chezbob.finance.views.transaction_dump'),
)
