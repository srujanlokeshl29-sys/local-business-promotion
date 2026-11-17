from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer', index=True) # 'customer', 'owner', 'admin'
    preferred_language = db.Column(db.String(10), default='en')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    businesses = db.relationship('Business', backref='owner', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='author', lazy=True)
    enquiries = db.relationship('Enquiry', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def is_admin(self):
        return self.role == 'admin'
        
    def is_owner(self):
        return self.role == 'owner'
        
    def is_customer(self):
        return self.role == 'customer'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    kannada_name = db.Column(db.String(120), nullable=False)
    icon = db.Column(db.String(20), default='🏪')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    businesses = db.relationship('Business', backref='category', lazy=True)

class Business(db.Model):
    __tablename__ = 'businesses'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    business_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(80), nullable=False, default='Hiriyur')
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150))
    website = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending', index=True) # 'pending', 'approved', 'rejected'
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255), default='default_business.jpg')
    latitude = db.Column(db.Float, default=13.9450) # Geographic coordinates for live location tracking
    longitude = db.Column(db.Float, default=76.6210)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='business', lazy=True, cascade="all, delete-orphan")
    offers = db.relationship('Offer', backref='business', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='business', lazy=True, cascade="all, delete-orphan")
    enquiries = db.relationship('Enquiry', backref='business', lazy=True, cascade="all, delete-orphan")
    views = db.relationship('BusinessView', backref='business', lazy=True, cascade="all, delete-orphan")
    
    def update_rating(self):
        approved_reviews = [r for r in self.reviews if not r.is_reported]
        if approved_reviews:
            self.total_reviews = len(approved_reviews)
            self.rating = round(sum(r.rating for r in approved_reviews) / self.total_reviews, 1)
        else:
            self.total_reviews = 0
            self.rating = 0.0

    def distance_from(self, user_lat, user_lng):
        """Calculate distance in kilometers using the Haversine formula."""
        if not self.latitude or not self.longitude or user_lat is None or user_lng is None:
            return None
        import math
        try:
            u_lat = float(user_lat)
            u_lng = float(user_lng)
            R = 6371.0 # Earth's radius in km
            dlat = math.radians(self.latitude - u_lat)
            dlng = math.radians(self.longitude - u_lng)
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(u_lat)) * math.cos(math.radians(self.latitude)) *
                 math.sin(dlng / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return round(R * c, 2)
        except (ValueError, TypeError):
            return None

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(50), default='piece')
    image_url = db.Column(db.String(255), default='default_product.jpg')
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Offer(db.Model):
    __tablename__ = 'offers'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    discount_percent = db.Column(db.Numeric(5, 2), default=0.0)
    coupon_code = db.Column(db.String(50))
    valid_until = db.Column(db.Date, nullable=False)
    clicks_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    is_reported = db.Column(db.Boolean, default=False)
    report_reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Enquiry(db.Model):
    __tablename__ = 'enquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(150))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='new') # 'new', 'read', 'replied'
    reply_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BusinessView(db.Model):
    __tablename__ = 'business_views'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    ip_address = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    search_query = db.Column(db.String(200))
    category_filter = db.Column(db.String(100))
    location_filter = db.Column(db.String(100))
    searched_at = db.Column(db.DateTime, default=datetime.utcnow)
