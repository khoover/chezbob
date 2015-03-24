import os
from os.path import realpath, dirname, join
import sys
from parseEmail import parseEmailOrder, validOrder

mydir = dirname(realpath(__file__))

sys.path.append('/git/django/chezbob')
sys.path.append(realpath(join(mydir, '..', '..', '..' )))
sys.path.append(realpath(join(mydir, '..', '..', '..', 'django'  )))
sys.path.append(realpath(join(mydir, '..', '..', '..', 'django', 'chezbob' )))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from orders.models import Order, OrderItem

if __name__ == "__main__":
  if (len(sys.argv) == 2):
    txt =open(sys.argv[1]).read()
  else:
    print "Usage: %s [<filename.email>]" % (sys.argv[0])
    sys.exit(-1)

  order = parseEmailOrder(txt)
  assert validOrder(order)
