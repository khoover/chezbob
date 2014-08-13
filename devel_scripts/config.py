import os
from os.path import samefile, abspath, dirname
import sys
from common import error

basedir = abspath(dirname(__file__)) + '/../'
bob_dir = basedir + '/bob2k14/'
deploy_dir = basedir + '/deploy'

sys.path.append(bob_dir)

if ('VIRTUAL_ENV' not in os.environ or\
   not samefile(os.environ['VIRTUAL_ENV'], deploy_dir)):
  error("Script should be run from within a devel virtual environment")

from models import app, db, aggregate_purchases, products, transactions, users, userbarcodes

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(deploy_dir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(deploy_dir, 'db_repository')

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
