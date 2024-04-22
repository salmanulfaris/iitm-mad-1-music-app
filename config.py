import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = '23423rkhnskjhsdfkjlbhfsk'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PYTHONDONTWRITEBYTECODE='pycache.txt'
