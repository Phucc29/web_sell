from flask import Flask, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from config import Config
# 1. Import thêm thư viện Flask-Admin ở đầu file
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_admin.menu import MenuLink
import os
from flask_admin.form.upload import ImageUploadField
from markupsafe import Markup
from werkzeug.utils import secure_filename

db = SQLAlchemy()

class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('user_id') is not None and session.get('is_admin') == True
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
class OderAdminView(SecureModelView):
    form_choices = {'status': [('Đang chờ xử lý', 'Đang chờ xử lý'), ('Đang giao hàng', 'Đang giao hàng'), ('Đã hoàn thành','Đã hoàn thành')]}
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'uploads'))
class ProductAdminView(SecureModelView):
    # 1. Ghi đè ô nhập text thành công cụ Upload file ảnh
    form_extra_fields = {
        'image_url': ImageUploadField(
            'Hình ảnh sản phẩm',
            base_path = file_path,           # Nơi lưu file vật lý
            url_relative_path='uploads/',  # Đường dẫn tương đối dùng để hiển thị (tùy chọn)
            namegen=lambda obj, file_data: secure_filename(file_data.filename) # Làm sạch tên file
        )
    }

    # 2. (Tùy chọn) Hiển thị ảnh thu nhỏ (thumbnail) trong danh sách bảng thay vì hiện tên file
    def _list_thumbnail(view, context, model, name):
        if not model.image_url:
            return ''
        # Gọi file ảnh ra để hiển thị trên bảng của Flask-Admin
        return Markup(f'<img src="/static/uploads/{model.image_url}" style="width: 50px; height: 50px; object-fit: cover;">')

    column_formatters = {
        'image_url': _list_thumbnail
    }
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
        admin = Admin(
            app, 
            name='Quản trị hệ thống', 
            theme=Bootstrap4Theme(swatch='flatly'),
            endpoint='phuc_admin' 
        )
        admin.add_link(MenuLink(name='Về trang chủ', category='', url='/'))

        # 3. Thêm các bảng vào giao diện quản trị Admin
        admin.add_view(SecureModelView(User, db.session, name="Người dùng"))
        admin.add_view(ProductAdminView(Product, db.session, name="Sản phẩm"))
        admin.add_view(OderAdminView(Oder, db.session, name="Đơn hàng"))
        admin.add_view(SecureModelView(OderItem, db.session, name="Chi tiết Đơn"))
        
    return app
