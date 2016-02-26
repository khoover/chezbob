from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from os.path import expanduser

Session = sessionmaker()

def connect(url):
    e = create_engine(url)
    Session.configure(bind=e)
    return Session();


def connect_pgpass(host, port, user, db):
    def match(pat, val):
        if pat == "*" or pat == str(val):
            return True
        return False;

    with open(expanduser("~/.pgpass"), "r") as pgpass:
        passes = [ x.split(":") for x in pgpass]

    passwd = None

    for l in passes:
        if (match(l[0], host) and
            match(l[1], port) and
            match(l[2], db) and
            match(l[3], user)):
            passwd = l[4].strip()
            break

    if not passwd:
        raise Exception("Password for %s not found." % user)

    return connect("postgresql://%s:%s@%s:%d/%s" % (user, passwd, host, port, db));

if (__name__ == "__main__"):
    s = connect_pgpass('localhost', 5432, 'bob', 'bob')
