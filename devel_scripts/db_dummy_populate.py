#! /usr/bin/env python
from config import SQLALCHEMY_DATABASE_URI
from models import db, app, users
import os.path
from crypt import crypt

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

u = users(username="dimo", email="dummy", nickname="dummy", pwd=crypt("dummy", 'cB'), balance=0, disabled=False)

db.session.add(u)


db.session.commit()


