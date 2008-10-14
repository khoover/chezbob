import crypt

user_profile_variables = [
        {"name": "Auto Logout",
         "default": -1,
         "description": "Automatically log me out after a purchase"},
        {"name": "No Confirmation",
         "default": -1,
         "description": "Do not ask me to confirm a purchase"},
        {"name": "Speech",
         "default": -1,
         "description": "Verbally greet me and confirm purchases"},
        {"name": "Privacy",
         "default": -1,
         "description": "Do not record the exact products I buy"}
                        ]

class User:
    check_password = True
    salt = "cB"

    def __init__(self, userdata, password):
        self._loadFromUserData(userdata)
        self.password = password
        self.profile_variables = {}

        for var in user_profile_variables:
            self.profile_variables[var["name"]] = var["default"]

        print self.profile_variables

    def hasPassword(self):
        return self.check_password and self.password is not None

    def checkPassword(self, clear_password):
        if self.password is None:
            return True
        else:
            self.salt = self.password[-2:]
            crypted = crypt.crypt(clear_password, self.password)
            return crypted == self.password


    def _loadFromUserData(self, userdata):
        self.userid = userdata["userid"]
        self.username = userdata["username"]
        self.email = userdata["email"]
        self.userbarcode = userdata["userbarcode"]
        self.nickname = userdata["nickname"]

    def _setProfileVariable(self, name, value):
        self.profile_variables[name] = value
        print self.profile_variables
