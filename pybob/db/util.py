from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Session = sessionmaker()

def connect(url):
    e = create_engine(url)
    Session.configure(bind=e)
    return Session();
    
