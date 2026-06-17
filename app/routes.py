from flask import current_app as app, jsonify
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.models import CartItem, Product, User, Oder, OderItem
import traceback
import logging

@app.route("/")
def home():
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=6, error_out=False) 
    return render_template('index.html', products=products)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exist = User.query.filter_by(username = username).first()
        email_exist = User.query.filter_by(email=email).first()

        if user_exist:
            flash('Tên đăng nhập đã tồn tại', 'danger')
            return redirect(url_for('register'))
        if email_exist:
            flash('Email này đã tồn tại', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        flash('Đăng ký thành công', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            if user.is_admin:
                return redirect(url_for('phuc_admin.index'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect('login')

@app.route('/product_id/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/api/cart/add/<int:product_id>', methods = ['POST'])
def api_add_to_cart(product_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'})
    if session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Lỗi: Quản trị viên không thể đặt hàng!'})
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    quantity = int(data.get('quantity', 1))
    user_id = session['user_id']
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    current_qty_in_cart = cart_item.quantity if cart_item else 0
    new_total_qty = current_qty_in_cart + quantity
    if new_total_qty > product.stock:
        return jsonify({
            'success': False,
            'message': f'Rất tiếc, kho chỉ còn {product.stock} sản phẩm.'
        })
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    db.session.commit()
    cart_count = sum(item.quantity for item in CartItem.query.filter_by(user_id=user_id).all())
    return jsonify({'success':True, 'cart_count': cart_count})

@app.route('/api/cart/count')
def cart_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    if session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Lỗi!'})
    count = sum(
        item.quantity
        for item in CartItem.query.filter_by(
            user_id=session['user_id']
        ).all()
    )
    return jsonify({'count': count})

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('is_admin'):
        return redirect(url_for('phuc_admin.index'))
    user_id = session['user_id']
    cart_items = db.session.query(CartItem, Product).join(Product, CartItem.product_id == Product.id).filter(CartItem.user_id == user_id).all()
    total_amount = sum(product.price * item.quantity for item, product in cart_items)
    total_quantity = sum(item[0].quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount, total_quantity=total_quantity)

# Chưa hiểu
@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    item = CartItem.query.get(item_id)
    if item and item.user_id == session.get('user_id'):
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('cart'))

@app.route('/checkout', methods = ['GET','POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('is_admin'):
        return redirect(url_for('phuc_admin.index'))
    user_id = session['user_id']
    cart_items = db.session.query(CartItem, Product).join(Product, CartItem.product_id == Product.id).filter(CartItem.user_id == user_id).all()
    total_amount = sum(product.price * item.quantity for item, product in cart_items)

    if not cart_items and request.method == 'GET':
        return redirect(url_for('cart'))
    if request.method == 'POST':
        new_oder = Oder(user_id = user_id, total_amount = total_amount, status = 'Đang chờ xử lý')
        db.session.add(new_oder)
        db.session.flush()
        for item, product in cart_items:
            if product.stock < item.quantity:
                flash(f'Sản phẩm {product.name} chỉ còn {product.stock} trong kho, không đủ số lượng đặt hàng!', 'danger')
                return redirect(url_for('cart'))
            product.stock -= item.quantity
            item_total_money = product.price * item.quantity
            new_item = OderItem(oder_id = new_oder.id, product_id = product.id, quantity=item.quantity, total_money = item_total_money)
            db.session.add(new_item)
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return redirect(url_for('order_history'))
    
    return render_template('checkout.html', cart_items = cart_items, total_amount = total_amount)

@app.route('/orders')
def order_history():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    if session.get('is_admin'):
        return redirect(url_for('phuc_admin.index'))
    user_oders = Oder.query.filter_by(user_id = user_id).order_by(Oder.created_at.desc()).all()
    return render_template('orders.html', oders = user_oders)

@app.route('/order/<int:oder_id>')
def order_detail(oder_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('is_admin'):
        return redirect(url_for('phuc_admin.index'))
    user_id = session.get('user_id')
    oder = Oder.query.filter_by(id = oder_id, user_id = user_id).first_or_404()
    oder_items = db.session.query(OderItem, Product).join(Product, OderItem.product_id == Product.id).filter(OderItem.oder_id == oder_id).all()
    return render_template('order_detail.html', oder = oder, oder_items=oder_items)

@app.route('/api/cart/update/<int:item_id>', methods=['POST'])
def update_cart_item(item_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập!'})
    if session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Admin không có giỏ hàng!'})
    user_id = session.get('user_id')
    cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not cart_item:
        return jsonify({'success': False, 'message': 'Không tìm thấy sản phẩm trong giỏ!'}), 404
    data = request.get_json()
    new_qty = int(data.get('quantity', 1))
    if new_qty < 1:
        return jsonify({'success': False, 'message': 'Số lượng không hợp lệ!'}), 400
    warning_msg = None
    product = Product.query.get(cart_item.product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại!'}), 400
    if new_qty > product.stock:
        new_qty = product.stock
        warning_msg = f'Rất tiếc, kho chỉ còn {product.stock} sản phẩm.'
    cart_item.quantity = new_qty
    db.session.commit()
    all_items = db.session.query(CartItem, Product).join(Product, CartItem.product_id == Product.id).filter(CartItem.user_id == user_id).all()
    new_total_amount = sum(product.price * item.quantity for item, product in all_items)

    cart_count = sum(item.quantity for item in CartItem.query.filter_by(user_id=user_id).all())
    return jsonify({
        'success': True,
        'message': warning_msg, # Có thể có chữ hoặc là None
        'updated_qty': new_qty, # Gửi số lượng chính thức về cho Frontend
        'new_total_amount': new_total_amount,
        'cart_count': cart_count
    })

@app.route('/api/search', methods=['GET'])
def api_search():
    # Lấy từ khóa 'q' khách gõ trên thanh tìm kiếm (ví dụ: /api/search?q=tai+nghe)
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([]) # Nếu trống thì trả về danh sách rỗng
        
    # Tìm kiếm trong DB: Tên sản phẩm chứa từ khóa (Không phân biệt hoa thường với ilike)
    # Nếu dùng SQLite thì dùng .like(), dùng PostgreSQL thì dùng .ilike() cho chuẩn nhé
    products = Product.query.filter(Product.name.ilike(f'%{query}%')).limit(5).all()
    
    # Chuyển đổi danh sách kết quả thành dạng JSON để gửi về cho JavaScript đọc
    results = []
    for p in products:
        results.append({
            'id': p.id,
            'name': p.name,
            'price': "{:,.0f}".format(p.price) + " ₫",
            'image_url': p.image_url
        })
    return jsonify(results)

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Dữ liệu không tồn tại hoặc sai đường dẫn!'}), 404
    return redirect(url_for('home'))
@app.errorhandler(405)
def method_not_allowed_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Phương thức truy cập không được phép!'}), 404
    return redirect(url_for('home'))

@app.errorhandler(Exception)
def internal_error(error):
    try:
        db.session.rollback()
    except Exception:
        pass
    logging.basicConfig(filename='app_errors.log', level=logging.ERROR, format='\n--- %(asctime)s ---\n%(message)s')
    logging.error(f"Lỗi ở đường dẫn: {request.path}\n{traceback.format_exc()}")
    if app.debug:
        raise error
        
    # NẾU ĐÃ ĐƯA LÊN MẠNG (Debug = False) -> Giấu code, trả về thông báo thân thiện
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False, 
            'message': 'Hệ thống đang gặp sự cố. Lỗi đã được ghi nhận, vui lòng thử lại sau!'
        }), 500
        
    flash('Đã xảy ra sự cố hệ thống không mong muốn. Đội ngũ kỹ thuật đã ghi nhận lỗi!', 'danger')
    return redirect(url_for('home'))