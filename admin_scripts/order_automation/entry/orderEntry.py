import os
import sys

mydir = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(mydir, '..', '..', '..' ))
sys.path.append(os.path.join(mydir, '..', '..', '..', 'django'  ))
sys.path.append(os.path.join(mydir, '..', '..', '..', 'django', 'chezbob' ))
sys.path.append(os.path.join(mydir, '..', '..', '..', 'django', 'chezbob', 'orders' ))

os.environ = '/git/django/settings.py'

print sys.path

import models
