from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Default admin interface for editing database
    (r'^admin/', include('django.contrib.admin.urls')),

    (r'^products/', 'chezbob.bobdb.views.products'),
)
