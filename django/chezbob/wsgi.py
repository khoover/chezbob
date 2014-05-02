#!/usr/bin/env python

import os
import sys
sys.path.append("/srv/www/django")
sys.path.append("/srv/www/django/chezbob")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chezbob.settings")

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
