from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) #nạp cấu hình
    db.init_app(app) #gắn db vào app
    #import routes tránh lỗi vòng lặp
    with app.app_context():
        from app import routes, models
    return app