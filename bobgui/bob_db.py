import sys, os, string
from pyPgSQL import PgSQL
from user import *

# bob=> \d users
#            Table "public.users"
#   Column    |       Type        | Modifiers 
#-------------+-------------------+-----------
# userid      | integer           | not null
# username    | character varying | not null
# email       | character varying | not null
# userbarcode | character varying | 
# nickname    | character varying | 
#
#  bob=> \d pwd
#           Table "public.pwd"
# Column |       Type        | Modifiers 
#--------+-------------------+-----------
# userid | integer           | not null
# p      | character varying | 
#
#bob=> \d profiles
#         Table "public.profiles"
#  Column  |       Type        | Modifiers 
#----------+-------------------+-----------
# userid   | integer           | not null
# property | character varying | not null
# setting  | integer           | not null


class BobDB:
    def __init__(self):
        self.db = None

        self.connect()
    
    def connect(self):
        # XXX
        if self.db is None:
            self.db = PgSQL.connect(host="soda.ucsd.edu", 
                                    database="bob")
            # XXX
            self.db.debug="text"

    def getUserByUserName(self, username):
        self.connect()
        st = self.db.cursor()

        # Grab Userdata
        st.execute("select * from users where username=%s", username)

        userdata = st.fetchone()

        if userdata is None:
            return None

        # Grab the PW
        st.execute("select p from pwd where userid=%s", userdata["userid"])

        password = None
        res = st.fetchone()
        if res is not None:
            password = res["p"]

        user = User(userdata, password)

        # Grab preferences
        st.execute("select property, setting from profiles where userid=%s",
                   userdata["userid"])

        res = st.fetchone()
        while res:
            user._setProfileVariable(res["property"], res["setting"])
            res = st.fetchone()

        # Grab balance
        st.execute("select balance from balances where userid=%s",
                   userdata["userid"])
        
        res = st.fetchone()
        if res:
            user._setBalance(res["balance"])

        self.db.commit()

        return user

