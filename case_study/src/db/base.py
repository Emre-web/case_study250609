from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL

Base = declarative_base()

def get_engine():
    return create_engine(DATABASE_URL)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
