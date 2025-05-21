from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from bookstore_flask_project.app import db # Import db instance from app/__init__.py

# Association table for Many-to-Many between Order and Book (if using that approach)
# order_books = db.Table('order_books',
#     db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
#     db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
#     db.Column('quantity', db.Integer, nullable=False, default=1),
#     db.Column('price_at_purchase', db.Float, nullable=False)
# )

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for bcrypt
    role = db.Column(db.String(20), default='customer', nullable=False) # 'customer' or 'manager'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='customer', lazy='dynamic')
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic', cascade="all, delete-orphan")


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None: # Handle users created without a password (e.g. social login placeholder)
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False, index=True)
    author = db.Column(db.String(140), index=True)
    isbn = db.Column(db.String(20), unique=True, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    cover_image_filename = db.Column(db.String(255)) # e.g., 'my_book_cover.jpg'
    category = db.Column(db.String(50), index=True)
    publication_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship for OrderItem
    order_items = db.relationship('OrderItem', backref='book_item', lazy='dynamic')

    def __repr__(self):
        return f'<Book {self.title}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    order_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True) # e.g., pending, paid, processing, shipped, delivered, cancelled
    # Shipping Address details
    shipping_name = db.Column(db.String(100))
    shipping_address1 = db.Column(db.String(200))
    shipping_address2 = db.Column(db.String(200))
    shipping_city = db.Column(db.String(100))
    shipping_state = db.Column(db.String(100))
    shipping_zip_code = db.Column(db.String(20))
    shipping_country = db.Column(db.String(100))

    # Relationship to OrderItem
    items = db.relationship('OrderItem', backref='order_ref', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Order {self.id} - Status: {self.status}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_purchase = db.Column(db.Float, nullable=False) # Price of the book when the order was made

    def __repr__(self):
        return f'<OrderItem Order: {self.order_id} Book: {self.book_id} Qty: {self.quantity}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define a unique constraint for user_id and book_id
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='_user_book_uc'),)

    book = db.relationship('Book', backref='cart_associations') # Easy access to book details

    def __repr__(self):
        return f'<CartItem User: {self.user_id} Book: {self.book_id} Qty: {self.quantity}>'