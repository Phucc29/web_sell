from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique = True, nullable = False)
    password = db.Column(db.String(1000), nullable = False)
    email = db.Column(db.String(70), unique = True, nullable = False)

    cart = db.relationship('CartItem', backref = 'user', lazy = True)
    orders = db.relationship('Oder', backref = 'user', lazy = True)

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    des = db.Column(db.Text, nullable = False)
    price = db.Column(db.Integer, nullable = False)
    stock = db.Column(db.Integer, nullable = False, default = 0)
    image_url = db.Column(db.Text, nullable = False)

class CartItem(db.Model):
    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete = 'CASCADE'), nullable = False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete = 'CASCADE'), nullable = False)
    quantity = db.Column(db.Integer, nullable = False, default = 1)

class Oder(db.Model):
    __tablename__ = 'oders'

    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete = 'CASCADE'), nullable = False)
    total_amount = db.Column(db.Numeric(10,2), nullable = False)
    status = db.Column(db.String(100), nullable = False, default = 'Đang chờ xử lý')
    created_at = db.Column(db.DateTime, default = datetime.now)

    item = db.relationship('OderItem', backref = 'oder', lazy = True)
    
class OderItem(db.Model):
    __tablename__ = 'oder_item'

    id = db.Column(db.Integer, primary_key = True)
    oder_id = db.Column(db.Integer, db.ForeignKey('oders.id', ondelete = 'CASCADE'), nullable = False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable = False)
    quantity = db.Column(db.Integer, nullable = False)
    total_money = db.Column(db.Numeric(10, 2), nullable = False)
