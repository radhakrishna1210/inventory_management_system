from flask import Blueprint, render_template, request, redirect, url_for, flash, json, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Product, Batch, Bill, BillItem, Category, ProductImage, User
from app import ml_models
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to ensure only admin users can access the route."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, User):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

def save_picture(form_picture):
    """Saves a picture to the filesystem."""
    filename = secure_filename(form_picture.filename)
    picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    form_picture.save(picture_path)
    return filename

@admin.route('/dashboard')
@admin_required
def dashboard():
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    daily_sales = db.session.query(
        func.date(Bill.date).label('sale_date'),
        func.sum(Bill.final_amount).label('total_sales')
    ).filter(Bill.date >= thirty_days_ago).group_by('sale_date').order_by('sale_date').all()
    
    sales_chart_labels = [sale.sale_date.strftime('%b %d') for sale in daily_sales]
    sales_chart_data = [str(sale.total_sales) for sale in daily_sales]

    top_products_by_revenue = db.session.query(
        BillItem.product_name,
        func.sum(BillItem.price_per_unit * BillItem.quantity).label('total_revenue')
    ).group_by(BillItem.product_name).order_by(db.desc('total_revenue')).limit(5).all()

    top_products_by_units = db.session.query(
        BillItem.product_name,
        func.sum(BillItem.quantity).label('total_units')
    ).group_by(BillItem.product_name).order_by(db.desc('total_units')).limit(5).all()
    
    revenue_by_category = db.session.query(
        Category.name,
        func.sum(BillItem.price_per_unit * BillItem.quantity).label('total_revenue')
    ).join(Product, BillItem.product_id == Product.id).join(Category).group_by(Category.name).order_by(db.desc('total_revenue')).all()

    category_chart_labels = [item.name for item in revenue_by_category]
    category_chart_data = [str(item.total_revenue) for item in revenue_by_category]

    all_customers = db.session.query(Bill.customer_email).distinct().all()
    customer_emails = [c[0] for c in all_customers if c[0]]
    customer_bill_counts = db.session.query(
        Bill.customer_email,
        func.count(Bill.id).label('bill_count')
    ).filter(Bill.customer_email.isnot(None)).group_by(Bill.customer_email).all()
    
    new_customers = sum(1 for _, count in customer_bill_counts if count == 1)
    returning_customers = sum(1 for _, count in customer_bill_counts if count > 1)

    return render_template('admin/dashboard.html',
                           sales_chart_labels=json.dumps(sales_chart_labels),
                           sales_chart_data=json.dumps(sales_chart_data),
                           top_products_by_revenue=top_products_by_revenue,
                           top_products_by_units=top_products_by_units,
                           category_chart_labels=json.dumps(category_chart_labels),
                           category_chart_data=json.dumps(category_chart_data),
                           new_customers=new_customers,
                           returning_customers=returning_customers)

@admin.route('/products', methods=['GET', 'POST'])
@admin_required
def manage_products():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        category_name = request.form.get('category_name', '').strip()

        if name and price and category_name:
            # Get or create category
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
                db.session.flush()
            
            new_product = Product(name=name, price=Decimal(price), description=description, category_id=category.id)
            db.session.add(new_product)
            db.session.flush()

            uploaded_files = request.files.getlist('images[]')
            for file in uploaded_files:
                if file and file.filename != '':
                    image_filename = save_picture(file)
                    new_image = ProductImage(image_filename=image_filename, product_id=new_product.id)
                    db.session.add(new_image)
            
            db.session.commit()
            flash('Product added successfully!', 'success')
        else:
            flash('Name, price, and category are required.', 'danger')
        return redirect(url_for('admin.manage_products'))
    
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)

@admin.route('/product/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = Decimal(request.form.get('price'))
        
        # Get or create category
        category_name = request.form.get('category_name', '').strip()
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
                db.session.flush()
            product.category_id = category.id
        
        uploaded_files = request.files.getlist('images[]')
        for file in uploaded_files:
            if file and file.filename != '':
                image_filename = save_picture(file)
                new_image = ProductImage(image_filename=image_filename, product_id=product.id)
                db.session.add(new_image)
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.manage_products'))
    
    categories = Category.query.all()
    return render_template('admin/edit_product.html', product=product, categories=categories)

@admin.route('/product/delete/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'danger')
    return redirect(url_for('admin.manage_products'))

@admin.route('/product/image/delete/<int:image_id>', methods=['POST'])
@admin_required
def delete_product_image(image_id):
    image = ProductImage.query.get_or_404(image_id)
    product_id = image.product.id
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted successfully.', 'success')
    return redirect(url_for('admin.edit_product', id=product_id))

@admin.route('/categories', methods=['GET', 'POST'])
@admin_required
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            new_category = Category(name=name)
            db.session.add(new_category)
            db.session.commit()
            flash('Category added successfully!', 'success')
        return redirect(url_for('admin.manage_categories'))
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin.route('/billing')
@admin_required
def billing():
    products_query = Product.query.order_by(Product.name).all()
    products_list = [{"id": p.id, "name": p.name, "price": str(p.price), "stock": p.stock} for p in products_query]
    return render_template('admin/billing.html', products_json=json.dumps(products_list))

@admin.route('/billing/create', methods=['POST'])
@admin_required
def create_bill():
    try:
        customer_name = request.form.get('customer_name')
        product_ids = [int(pid) for pid in request.form.getlist('product_id[]')]
        quantities = [int(q) for q in request.form.getlist('quantity[]')]
        tax_percentage = Decimal(request.form.get('tax_percentage', '0'))
        discount_amount = Decimal(request.form.get('discount_amount', '0'))
        
        products_for_bill = db.session.query(Product).filter(Product.id.in_(product_ids)).with_for_update().all()
        products_dict = {p.id: p for p in products_for_bill}

        subtotal = Decimal('0.0')
        bill_items_to_create = []

        for i, product_id in enumerate(product_ids):
            quantity_to_sell = quantities[i]
            product = products_dict.get(product_id)
            
            if not product or product.stock < quantity_to_sell:
                flash(f'Not enough stock for {product.name}. Only {product.stock} available.', 'danger')
                db.session.rollback()
                return redirect(url_for('admin.billing'))

            for batch in sorted(product.batches, key=lambda b: b.id):
                if quantity_to_sell > 0:
                    sell_from_batch = min(quantity_to_sell, batch.quantity)
                    batch.quantity -= sell_from_batch
                    quantity_to_sell -= sell_from_batch
            
            item_total = product.price * quantities[i]
            subtotal += item_total
            bill_items_to_create.append({
                "product_id": product.id, "name": product.name, 
                "quantity": quantities[i], "price": product.price
            })

        tax_amount = subtotal * (tax_percentage / 100)
        final_amount = (subtotal + tax_amount) - discount_amount

        new_bill = Bill(customer_name=customer_name, subtotal=subtotal, tax_percentage=tax_percentage,
                        discount_amount=discount_amount, final_amount=final_amount)
        db.session.add(new_bill)
        db.session.flush()

        for item in bill_items_to_create:
            bill_item = BillItem(bill_id=new_bill.id, product_id=item['product_id'],
                                 product_name=item['name'], quantity=item['quantity'], 
                                 price_per_unit=item['price'])
            db.session.add(bill_item)
        
        db.session.commit()
        flash('Bill generated successfully!', 'success')
        return redirect(url_for('admin.bill_detail', id=new_bill.id))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('admin.billing'))

@admin.route('/bill/<int:id>')
@admin_required
def bill_detail(id):
    bill = Bill.query.get_or_404(id)
    return render_template('admin/bill_detail.html', bill=bill)

@admin.route('/inventory', methods=['GET', 'POST'])
@admin_required
def manage_inventory():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        if product_id and quantity:
            new_batch = Batch(product_id=int(product_id), quantity=int(quantity))
            db.session.add(new_batch)
            db.session.commit()
            flash('Inventory batch added!', 'success')
        return redirect(url_for('admin.manage_inventory'))
        
    batches = Batch.query.all()
    products = Product.query.all()
    return render_template('admin/inventory.html', batches=batches, products=products)

@admin.route('/inventory/summary')
@admin_required
def inventory_summary():
    inventory = db.session.query(
        Product.name, Product.description, Product.id,  
        func.sum(Batch.quantity).label('total_quantity')
    ).outerjoin(Batch).group_by(Product.id).all()
    return render_template('admin/inventory_summary.html', inventory=inventory)

@admin.route('/forecasting')
@admin_required
def forecasting():
    predicted_demand = ml_models.predict_future_demand()
    return render_template('admin/forecasting.html', prediction=predicted_demand)

@admin.route('/train-model')
@admin_required
def train_model_route():
    ml_models.train_and_save_demand_model()
    flash('Demand forecasting model has been re-trained.', 'success')
    return redirect(url_for('admin.forecasting'))

