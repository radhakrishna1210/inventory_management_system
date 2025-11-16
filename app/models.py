from decimal import Decimal
from . import db
from sqlalchemy.sql import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    # Try to load as admin User first, then as Customer
    user = User.query.get(int(user_id))
    if user:
        return user
    return Customer.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Customer(db.Model, UserMixin):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Customer {self.email}>'

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    images = db.relationship('ProductImage', backref='product', lazy=True, cascade="all, delete-orphan")
    batches = db.relationship('Batch', backref='product', lazy=True, cascade="all, delete-orphan")

    @property
    def stock(self):
        return sum(batch.quantity for batch in self.batches)

    @property
    def primary_image(self):
        if self.images:
            return self.images[0].image_filename
        return 'placeholder.jpg'

    def __repr__(self):
        return f'<Product {self.name}>'

class ProductImage(db.Model):
    __tablename__ = 'product_image'
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    def __repr__(self):
        return f'<Image {self.image_filename} for Product ID {self.product_id}>'

class Batch(db.Model):
    __tablename__ = 'batch'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Batch {self.id} with {self.quantity} units>'

class Bill(db.Model):
    __tablename__ = 'bill'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_email = db.Column(db.String(150), nullable=True)
    customer_address = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_percentage = db.Column(db.Numeric(5, 2), nullable=False, default=Decimal('0.00'))
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    final_amount = db.Column(db.Numeric(10, 2), nullable=False)
    items = db.relationship('BillItem', backref='bill', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Bill {self.id} for {self.customer_name}>'

class BillItem(db.Model):
    __tablename__ = 'bill_item'
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<BillItem {self.product_name} (x{self.quantity})>'
