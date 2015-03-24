import os
from os.path import realpath, dirname, join
import sys

mydir = dirname(realpath(__file__))

sys.path.append('/git/django/chezbob')
sys.path.append(realpath(join(mydir, '..', '..', '..' )))
sys.path.append(realpath(join(mydir, '..', '..', '..', 'django'  )))
sys.path.append(realpath(join(mydir, '..', '..', '..', 'django', 'chezbob' )))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

print sys.path

import orders.models
