from flask import Flask, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from config import Config
# 1. Import thêm thư viện Flask-Admin ở đầu file
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

db = SQLAlchemy()

class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('user_id') is not None and session.get('is_admin') == True
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
class OderAdminView(SecureModelView):
    form_choices = {'status': [('Đang chờ xử lý', 'Đang chờ xử lý'), ('Đang giao hàng', 'Đang giao hàng'), ('Đã hoàn thành','Đã hoàn thành')]}
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) # nạp cấu hình
    db.init_app(app) # gắn db vào app
    
    # import routes tránh lỗi vòng lặp
    with app.app_context():
        # Import các model của bạn từ file models.py ra để dùng
        from app import routes, models
        from app.models import User, Product, Oder, OderItem # Nhớ sửa lại đường dẫn import cho đúng cấu trúc folder của bạn

        # 2. Khởi tạo Admin nằm gọn trong Context của App
        admin = Admin(app, name='PhucShop Admin')

        # 3. Thêm các bảng vào giao diện quản trị Admin
        admin.add_view(SecureModelView(User, db.session, name="Người dùng"))
        admin.add_view(SecureModelView(Product, db.session, name="Sản phẩm"))
        admin.add_view(OderAdminView(Oder, db.session, name="Đơn hàng"))
        admin.add_view(SecureModelView(OderItem, db.session, name="Chi tiết Đơn"))
        
    return app
