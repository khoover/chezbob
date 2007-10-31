from django.conf.urls.defaults import *

urlpatterns = patterns('chezbob.cashout.views',
        (r'^(\d+)/$', 'edit_cashout'),
        (r'^new/$', 'edit_cashout'),
        (r'^ledger/$', 'ledger'),
        (r'^onhand/$', 'cashonhand'),
        (r'^$', 'ledger'),
        )
