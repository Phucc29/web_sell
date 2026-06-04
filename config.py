import os

class Config:
    SECRET_KEY = '123454321'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1@localhost/ecommerce_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False