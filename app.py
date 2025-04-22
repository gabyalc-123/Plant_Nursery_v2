from flask import render_template, redirect, request, session, url_for, Flask, jsonify
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import random
import string
from werkzeug.utils import secure_filename

from models import init_app, db
from models.user import User
from models.plant_type import PlantType
from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from models.care_instruction import CareInstruction
import json

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_KEY_PREFIX'] = 'hello'
app.config['SESSION_COOKIE_NAME'] = 'fuel_quote_session'
app.secret_key = "Kc5c3zTk'-3<&BdL:P92O{_(:-NkY+"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
init_app(app)


@app.route('/')
def welcome():
    return render_template('index.html')
    # return "🌿 Welcome to the Online Plant Nursery API!"


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        role = request.form.get('role')

        if not username or not email or not password or not role:
            return render_template('register.html', error="All fields are required")

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")

        user = User(username=username, email=email, password=password, role=role, created_at=datetime.now())
        try:
            db.session.add(user)
            db.session.commit()
            db.session.close()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error="Email already registered or internal error")

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')


@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('role') != 'customer':
        return redirect(url_for('login'))
    return render_template('user/dashboard.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/product_details/<int:product_id>')
def product_details(product_id):
    if 'user_id' not in session:
        return redirect('/login')

    product = Product.query.get_or_404(product_id)
    plant_type = PlantType.query.get(product.plant_type_id)
    care = CareInstruction.query.filter_by(product_id=product_id).first()
    is_admin = session.get('role') == 'admin'

    return render_template('user/product_details.html',
                           product=product,
                           plant_type=plant_type,
                           care=care,
                           is_admin=is_admin)


@app.route('/cart')
def show_cart():
    return render_template('user/cart.html')


# @app.route('/place_order', methods=['POST'])
# def place_order():
#     try:
#         user_id = request.form.get('user_id')
#         items = json.loads(request.form.get('items'))
#
#         if not user_id or not items:
#             return jsonify({'error': 'Missing user_id or items'}), 400
#
#         # Calculate total amount
#         total_amount = 0
#         for item in items:
#             product = Product.query.get(item['product_id'])
#             if product:
#                 total_amount += product.price * int(item['quantity'])
#
#         # Insert order
#         order = Order(user_id=user_id, total_amount=total_amount, status='Pending', order_date=datetime.now())
#         db.session.add(order)
#         db.session.commit()
#
#         # Insert order items
#         for item in items:
#             product = Product.query.get(item['product_id'])
#             if product:
#                 order_item = OrderItem(
#                     order_id=order.id,
#                     product_id=product.id,
#                     quantity=item['quantity'],
#                     price=product.price
#                 )
#                 db.session.add(order_item)
#
#         db.session.commit()
#         return jsonify({'message': 'Order placed successfully'}), 201
#
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'error': 'Order failed', 'details': str(e)}), 500

@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        user_id = request.form.get('user_id')
        items = json.loads(request.form.get('items'))

        if not user_id or not items:
            return jsonify({'error': 'Missing user_id or items'}), 400

        # Calculate total amount and validate stock
        total_amount = 0
        for item in items:
            product = Product.query.get(item['product_id'])
            quantity = int(item['quantity'])
            if not product:
                return jsonify({'error': f'Product not found for ID {item["product_id"]}'}), 400

            if product.stock < quantity:
                return jsonify({
                    'error': f'Insufficient stock for \"{product.name}\". Available: {product.stock}, '
                             f'Requested: {quantity}'}), 400
            total_amount += product.price * quantity

        # Insert order
        order = Order(user_id=user_id, total_amount=total_amount, status='Pending', order_date=datetime.now())
        db.session.add(order)
        db.session.commit()

        # Insert order items and update stock
        for item in items:
            product = Product.query.get(item['product_id'])
            quantity = int(item['quantity'])
            if product:
                product.stock -= quantity
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price
                )
                db.session.add(order_item)

        db.session.commit()
        return jsonify({'message': 'Order placed successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Order failed', 'details': str(e)}), 500


@app.route('/orders')
def user_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.order_date.desc()).all()
    return render_template('user/orders.html', orders=orders)


@app.route('/get_order_details/<int:order_id>')
def view_order_details(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session.get('role')

    if role == 'admin':
        order = Order.query.get(order_id)
    else:
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return "Order not found or access denied", 404

    order_items_raw = OrderItem.query.filter_by(order_id=order.id).all()
    products = {p.id: p for p in Product.query.all()}

    order_items = []
    for item in order_items_raw:
        product = products.get(item.product_id)
        if product:
            order_items.append({
                'name': product.name,
                'image_url': product.image_url,
                'quantity': item.quantity,
                'price': item.price
            })

    return render_template(
        'user/order_details.html',
        order=order,
        order_items=order_items
    )



# @app.route('/cancel_order', methods=['POST'])
# def cancel_order():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
#
#     order_id = request.form.get('order_id')
#     order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first()
#
#     if not order:
#         return "Order not found or access denied", 404
#
#     if order.status.lower() in ['delivered', 'cancelled']:
#         return f"Cannot cancel order in '{order.status}' state", 400
#
#     # Restore stock
#     order_items = OrderItem.query.filter_by(order_id=order.id).all()
#     for item in order_items:
#         product = Product.query.get(item.product_id)
#         if product:
#             product.stock += item.quantity
#
#     order.status = 'Cancelled'
#     db.session.commit()
#     return redirect(f'/get_order_details/{order.id}')





@app.route('/admin/products')
def admin_products():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/products.html')


@app.route('/update_stock', methods=['POST'])
def update_stock():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    product_id = request.form.get('product_id')
    new_stock = request.form.get('stock')

    try:
        product = Product.query.get(int(product_id))
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        product.stock = int(new_stock)
        db.session.commit()
        return jsonify({'message': 'Stock updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update stock: {str(e)}'}), 500


@app.route('/admin/add_product', methods=['GET', 'POST'])
def admin_add_product():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        plant_type_id = int(request.form.get('plant_type_id'))
        image_file = request.files.get('image_url')

        image_url = ''
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_url = f"uploads/{filename}"

        new_product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            plant_type_id=plant_type_id,
            image_url=image_url,
            created_by=session['user_id'],
            created_at=datetime.now()
        )
        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect('/admin/products')
        except Exception as e:
            db.session.rollback()
            return f"Failed to add product: {str(e)}", 500

    # GET request – load plant types
    plant_types = PlantType.query.all()
    return render_template('admin/add_product.html', plant_types=plant_types)


@app.route('/admin/get_users_with_orders')
def get_users_with_orders():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify([]), 403

    users = User.query.all()
    orders = db.session.query(Order.user_id, db.func.count(Order.id)).group_by(Order.user_id).all()
    order_map = {user_id: count for user_id, count in orders}

    result = []
    for u in users:
        result.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'password': u.password,  # 🚨 Unsafe for real applications
            'role': u.role,
            'order_count': order_map.get(u.id, 0)
        })

    return jsonify(result)


@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user_id = request.form.get('user_id')
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500


@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/users.html')


@app.route('/admin/get_all_orders')
def admin_get_all_orders():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify([]), 403

    orders = Order.query.all()
    users = {u.id: u.username for u in User.query.all()}

    result = []
    for o in orders:
        result.append({
            'id': o.id,
            'user_id': o.user_id,
            'user_name': users.get(o.user_id, 'Unknown'),
            'order_date': o.order_date,
            'status': o.status,
            'total_amount': o.total_amount
        })

    return jsonify(result)


@app.route('/admin/cancel_order', methods=['POST'])
def admin_cancel_order():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)

    if not order or order.status.lower() in ['cancelled', 'delivered']:
        return jsonify({'error': 'Order cannot be cancelled'}), 400

    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    for item in order_items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock += item.quantity

    order.status = 'Cancelled'
    db.session.commit()
    return jsonify({'message': 'Order cancelled successfully'})


@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    role = session.get('role')
    order_id = request.form.get('order_id')

    if not order_id:
        return "Order ID required", 400

    # Allow admin to cancel any order, user can only cancel their own
    if role == 'admin':
        order = Order.query.get(order_id)
    else:
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return "Order not found or access denied", 404

    if order.status == 'Cancelled':
        return "Order is already cancelled", 400
    if order.status == 'Delivered':
        return "Delivered orders cannot be cancelled", 400

    # Restore stock
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    for item in order_items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock += item.quantity

    order.status = 'Cancelled'
    db.session.commit()

    return redirect(f"/get_order_details/{order_id}")



@app.route('/admin/mark_delivered', methods=['POST'])
def admin_mark_delivered():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)

    if not order or order.status.lower() in ['cancelled', 'delivered']:
        return jsonify({'error': 'Order cannot be marked as delivered'}), 400

    order.status = 'Delivered'
    db.session.commit()
    return jsonify({'message': 'Order marked as delivered'})


@app.route('/admin/orders')
def admin_orders():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/orders.html')






@app.route('/get_users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{k: v for k, v in u.__dict__.items() if not k.startswith('_')} for u in users])


# ---------------- Plant Types ----------------
@app.route('/insert_plant_type', methods=['POST'])
def insert_plant_type():
    type_name = request.form.get('type_name')
    description = request.form.get('description')
    plant_type = PlantType(
        type_name=type_name,
        description=description
    )
    try:
        db.session.add(plant_type)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating plant type", "error": str(e)}), 400
    return jsonify({"message": "Plant type added successfully."}), 201


@app.route('/get_plant_types', methods=['GET'])
def get_plant_types():
    types = PlantType.query.all()
    return jsonify([{k: v for k, v in t.__dict__.items() if not k.startswith('_')} for t in types])


@app.route('/admin/plant_types')
def admin_plant_types():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return render_template('admin/plant_types.html')


@app.route('/delete_plant_type', methods=['POST'])
def delete_plant_type():
    type_id = request.form.get('id')

    if not type_id:
        return jsonify({"message": "Plant type ID is required"}), 400

    plant_type = PlantType.query.get(type_id)

    if not plant_type:
        return jsonify({"message": "Plant type not found"}), 404

    try:
        db.session.delete(plant_type)
        db.session.commit()
        return jsonify({"message": "Plant type deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting plant type", "error": str(e)}), 500


# ---------------- Products ----------------
@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    plant_type_id = request.form.get('plant_type_id')
    stock = request.form.get('stock')
    created_by = request.form.get('created_by')
    file = request.files.get('image_url')

    image_url = None
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image_url = filepath

    product = Product(
        name=name,
        description=description,
        price=price,
        plant_type_id=plant_type_id,
        stock=stock,
        image_url=image_url,
        created_by=created_by,
        created_at=datetime.now()
    )
    try:
        db.session.add(product)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating product", "error": str(e)}), 400
    return jsonify({"message": "Product added successfully."}), 201


@app.route('/get_products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{k: v for k, v in p.__dict__.items() if not k.startswith('_')} for p in products])


# ---------------- Orders ----------------
@app.route('/add_order', methods=['POST'])
def add_order():
    user_id = request.form.get('user_id')
    total_amount = request.form.get('total_amount')
    status = request.form.get('status')

    order = Order(
        user_id=user_id,
        total_amount=total_amount,
        status=status,
        order_date=datetime.now()
    )
    try:
        db.session.add(order)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating order", "error": str(e)}), 400
    return jsonify({"message": "Order added successfully."}), 201


@app.route('/get_orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([{k: v for k, v in o.__dict__.items() if not k.startswith('_')} for o in orders])


# ---------------- Order Items ----------------
@app.route('/add_order_items', methods=['POST'])
def add_order_items():
    data = request.get_json()
    order_id = data.get('order_id')
    items = data.get('items')

    try:
        for item in items:
            order_item = OrderItem(
                order_id=order_id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)
        db.session.commit()
        db.session.close()
        return jsonify({"message": "Order items added successfully."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating order items", "error": str(e)}), 400


@app.route('/get_order_items', methods=['POST'])
def get_order_items():
    order_id = request.form.get('order_id')

    if not order_id:
        return jsonify({"error": "order_id is required"}), 400

    items = OrderItem.query.filter_by(order_id=order_id).all()
    item_list = [
        {
            "id": item.id,
            "order_id": item.order_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": item.price
        } for item in items
    ]
    return jsonify(item_list), 200


# ---------------- Care Instructions ----------------
@app.route('/add_care_instruction', methods=['POST'])
def add_care_instruction():
    product_id = request.form.get('product_id')
    instructions = request.form.get('instructions')
    care = CareInstruction(
        product_id=product_id,
        instructions=instructions
    )
    try:
        db.session.add(care)
        db.session.commit()
        db.session.close()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating care instruction", "error": str(e)}), 400
    return jsonify({"message": "Care instruction added successfully."}), 201


@app.route('/get_care_instructions', methods=['GET'])
def get_care_instructions():
    care_list = CareInstruction.query.all()
    return jsonify([{k: v for k, v in c.__dict__.items() if not k.startswith('_')} for c in care_list])


# ---------------- Cancel Order ----------------
@app.route('/cancel_order2', methods=['POST'])
def cancel_order2():
    order_id = request.form.get('order_id')

    if not order_id:
        return jsonify({"error": "order_id is required"}), 400

    order = Order.query.filter_by(id=order_id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    try:
        order.status = "Cancelled"
        db.session.commit()
        return jsonify({"message": "Order cancelled successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error cancelling order", "error": str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
