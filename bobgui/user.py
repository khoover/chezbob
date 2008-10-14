import crypt

class User:
    check_password = True
    salt = "cB"

    def __init__(self, userdata, password):
        self._loadFromUserData(userdata)
        self.password = password

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
