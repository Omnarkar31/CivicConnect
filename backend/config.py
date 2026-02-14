import os

class Config:
    SECRET_KEY = 'civicconnect_secret_key'
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:password@localhost/civic_connect_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'