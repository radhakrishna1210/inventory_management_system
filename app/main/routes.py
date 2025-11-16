from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user, login_required

from app import db
from app.models import Product, Bill, BillItem, User, Customer
from app.forms import LoginForm, CustomerLoginForm, CustomerSignupForm

main = Blueprint('main', __name__)

def _get_cart_contents():
    """Helper function to get cart contents and calculate total."""
    cart_items = []
    total_price = Decimal('0.0')
    
    cart_product_ids = [int(p_id) for p_id in session.get('cart', {}).keys()]
    if not cart_product_ids:
        return [], total_price

    # Fetch all products in the cart with one database query
    products = Product.query.filter(Product.id.in_(cart_product_ids)).all()
    product_map = {p.id: p for p in products}

    cart_session = session.get('cart', {})
    for product_id, quantity in cart_session.items():
        product = product_map.get(int(product_id))
        if product:
            item_total = product.price * quantity
            cart_items.append({'product': product, 'quantity': quantity, 'total': item_total})
            total_price += item_total
            
    return cart_items, total_price

@main.route('/')
def home():
    products = Product.query.order_by(Product.name).all()
    return render_template('home.html', products=products)

@main.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@main.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    product = Product.query.get_or_404(id)
    quantity = int(request.form.get('quantity', 1))
    product_id_str = str(product.id)
    
    cart = session.get('cart', {})
    current_quantity = cart.get(product_id_str, 0)
    
    if quantity > 0 and (current_quantity + quantity) <= product.stock:
        cart[product_id_str] = current_quantity + quantity
        flash(f'Added {quantity} x {product.name} to your cart.', 'success')
    else:
        flash(f'Sorry, only {product.stock} of {product.name} available.', 'danger')
        
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('main.product_detail', id=id))

@main.route('/cart')
def view_cart():
    cart_items, total_price = _get_cart_contents()
    return render_template('cart.html', cart_items=cart_items, total=total_price)

@main.route('/update_cart/<int:id>', methods=['POST'])
def update_cart(id):
    product = Product.query.get_or_404(id)
    quantity = int(request.form.get('quantity'))
    product_id_str = str(id)
    
    cart = session.get('cart', {})
    if product_id_str in cart:
        if quantity > 0 and quantity <= product.stock:
            cart[product_id_str] = quantity
        else:
            cart.pop(product_id_str, None) # Remove if quantity is 0 or invalid
            
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('main.view_cart'))

@main.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_items, total_price = _get_cart_contents()
    
    if not cart_items:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        customer_name = request.form.get('name')
        customer_email = request.form.get('email')
        customer_address = request.form.get('address')

        try:
            product_ids = [item['product'].id for item in cart_items]
            product_map = {p.id: p for p in db.session.query(Product).filter(Product.id.in_(product_ids)).with_for_update().all()}

            bill_items_to_create = []
            for item in cart_items:
                product = product_map.get(item['product'].id)
                if product.stock < item['quantity']:
                    flash(f'Not enough stock for {product.name}. Order cancelled.', 'danger')
                    db.session.rollback()
                    return redirect(url_for('main.view_cart'))
                
                # Deduct stock from batches
                remaining_to_sell = item['quantity']
                for batch in sorted(product.batches, key=lambda b: b.id):
                    if remaining_to_sell > 0:
                        sell_from_batch = min(remaining_to_sell, batch.quantity)
                        batch.quantity -= sell_from_batch
                        remaining_to_sell -= sell_from_batch
                
                bill_items_to_create.append(BillItem(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=item['quantity'],
                    price_per_unit=product.price
                ))
            
            new_bill = Bill(
                customer_name=customer_name, customer_email=customer_email,
                customer_address=customer_address, subtotal=total_price, final_amount=total_price,
                items=bill_items_to_create
            )
            db.session.add(new_bill)
            db.session.commit()
            
            session.pop('cart', None)
            return redirect(url_for('main.order_success', bill_id=new_bill.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during checkout: {e}', 'danger')
            return redirect(url_for('main.view_cart'))

    return render_template('checkout.html', cart_items=cart_items, total=total_price)

@main.route('/order_success/<int:bill_id>')
def order_success(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    return render_template('order_success.html', bill=bill)

@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    
    return render_template('login.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def customer_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = CustomerLoginForm()
    if form.validate_on_submit():
        customer = Customer.query.filter_by(email=form.email.data).first()
        if customer and customer.check_password(form.password.data):
            login_user(customer)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    
    return render_template('customer_login.html', form=form)

@main.route('/signup', methods=['GET', 'POST'])
def customer_signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = CustomerSignupForm()
    if form.validate_on_submit():
        # Check if customer already exists
        existing_customer = Customer.query.filter_by(email=form.email.data).first()
        if existing_customer:
            flash('An account with this email already exists. Please login instead.', 'danger')
            return redirect(url_for('main.customer_login'))
        
        # Create new customer
        new_customer = Customer(
            email=form.email.data,
            name=form.name.data
        )
        new_customer.set_password(form.password.data)
        
        db.session.add(new_customer)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('main.customer_login'))
    
    return render_template('customer_signup.html', form=form)

@main.route('/profile')
@login_required
def customer_profile():
    # Check if user is a customer (has email attribute)
    if not hasattr(current_user, 'email'):
        flash('Access denied. This page is for customers only.', 'danger')
        return redirect(url_for('main.home'))
    
    # Get customer's order history
    orders = Bill.query.filter_by(customer_email=current_user.email).order_by(Bill.date.desc()).limit(10).all()
    
    return render_template('customer_profile.html', customer=current_user, orders=orders)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))
