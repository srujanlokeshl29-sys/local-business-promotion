import os
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import func, desc, or_
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Category, Business, Product, Offer, Review, Enquiry, BusinessView, SearchHistory
from translations import get_translation
from init_db import seed_database
from ai_assistant import generate_ai_response

app = Flask(__name__)
app.config.from_object(Config)

# Try connecting to configured MySQL. If unavailable, smoothly fallback to local SQLite for development
try:
    from sqlalchemy import create_engine
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], connect_args={'connect_timeout': 1})
    with engine.connect() as conn:
        print("[DATABASE] Connected to MySQL database successfully.")
except Exception as e:
    print(f"[DATABASE NOTICE] MySQL connection unavailable ({e}). Falling back to local SQLite 'localbiz.db'.")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(Config.BASE_DIR, 'localbiz.db')

db.init_app(app)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Context Processor for Bilingual Kannada/English Translations & Global Data
@app.context_processor
def inject_global_context():
    lang = session.get('lang', 'en')
    categories = Category.query.all() if Category.query else []
    return {
        'current_lang': lang,
        '_t': lambda key: get_translation(key, lang),
        'nav_categories': categories,
        'current_year': datetime.now().year
    }

# Language Switcher Route
@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['en', 'kn']:
        session['lang'] = lang
        if current_user.is_authenticated:
            current_user.preferred_language = lang
            db.session.commit()
    referrer = request.referrer or url_for('home')
    return redirect(referrer)

# Role Access Control Decorators
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_owner() and not current_user.is_admin():
            flash('Access denied. Business owner account required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_customer() and not current_user.is_admin():
            flash('Access denied. Customer account required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# PUBLIC & DISCOVERY ROUTES
# ==============================================================================

@app.route('/')
def home():
    # Featured businesses (approved, highest rating)
    featured_businesses = Business.query.filter_by(status='approved').order_by(Business.rating.desc(), Business.view_count.desc()).limit(6).all()
    categories = Category.query.all()
    active_offers = Offer.query.filter_by(is_active=True).filter(Offer.valid_until >= date.today()).limit(4).all()
    
    # Calculate trending categories based on actual business count & views
    trending_cats = db.session.query(
        Category, func.count(Business.id).label('biz_count'), func.coalesce(func.sum(Business.view_count), 0).label('total_views')
    ).outerjoin(Business, (Business.category_id == Category.id) & (Business.status == 'approved'))\
     .group_by(Category.id)\
     .order_by(desc('biz_count'), desc('total_views'))\
     .limit(4).all()
    
    return render_template('index.html', 
                           featured_businesses=featured_businesses, 
                           categories=categories,
                           trending_cats=trending_cats,
                           active_offers=active_offers)

@app.route('/explore')
def explore():
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    city = request.args.get('city', '').strip()
    min_rating = request.args.get('rating', type=float)
    sort_by = request.args.get('sort', 'popular')
    
    # Record Search History if search parameters provided
    if query or category_id or city:
        cat_obj = db.session.get(Category, category_id) if category_id else None
        cat_name = cat_obj.name if cat_obj else None
        history = SearchHistory(
            user_id=current_user.id if current_user.is_authenticated else None,
            search_query=query if query else None,
            category_filter=cat_name,
            location_filter=city if city else None
        )
        db.session.add(history)
        db.session.commit()
        
    # Build query
    biz_query = Business.query.filter_by(status='approved')
    
    if query:
        search_term = f"%{query}%"
        biz_query = biz_query.filter(
            or_(
                Business.business_name.ilike(search_term),
                Business.description.ilike(search_term),
                Business.address.ilike(search_term),
                Business.products.any(Product.product_name.ilike(search_term))
            )
        )
        
    if category_id:
        biz_query = biz_query.filter(Business.category_id == category_id)
        
    if city and city != 'all':
        biz_query = biz_query.filter(Business.city.ilike(f"%{city}%"))
        
    if min_rating:
        biz_query = biz_query.filter(Business.rating >= min_rating)
        
    # Sort order
    if sort_by == 'rating':
        biz_query = biz_query.order_by(Business.rating.desc())
    elif sort_by == 'newest':
        biz_query = biz_query.order_by(Business.created_at.desc())
    elif sort_by == 'name':
        biz_query = biz_query.order_by(Business.business_name.asc())
    else: # popular
        biz_query = biz_query.order_by(Business.view_count.desc(), Business.rating.desc())
        
    # Location Tracking Filters (Near Me)
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', type=float)
    
    businesses = biz_query.all()
    
    # Calculate distances if coordinates provided
    if user_lat is not None and user_lng is not None:
        for b in businesses:
            b.user_distance = b.distance_from(user_lat, user_lng)
        if radius:
            businesses = [b for b in businesses if b.user_distance is not None and b.user_distance <= radius]
        if sort_by == 'nearest':
            businesses.sort(key=lambda b: (b.user_distance is None, b.user_distance or 999999))
    else:
        for b in businesses:
            b.user_distance = None

    categories = Category.query.all()
    
    # Get distinct cities in database for location filter
    cities = [r[0] for r in db.session.query(Business.city).filter_by(status='approved').distinct().all() if r[0]]
    if not cities:
        cities = ['Hiriyur', 'Chitradurga', 'Bengaluru']
        
    return render_template('explore.html',
                           businesses=businesses,
                           categories=categories,
                           cities=cities,
                           selected_category=category_id,
                           selected_city=city,
                           selected_query=query,
                           selected_rating=min_rating,
                           selected_sort=sort_by,
                           user_lat=user_lat,
                           user_lng=user_lng,
                           selected_radius=radius)

@app.route('/business/<int:business_id>')
def business_details(business_id):
    business = Business.query.get_or_404(business_id)
    
    # Track view count & log view event
    business.view_count = (business.view_count or 0) + 1
    view_log = BusinessView(
        business_id=business.id,
        ip_address=request.remote_addr,
        user_id=current_user.id if current_user.is_authenticated else None
    )
    db.session.add(view_log)
    db.session.commit()
    
    products = Product.query.filter_by(business_id=business.id, is_available=True).all()
    active_offers = Offer.query.filter_by(business_id=business.id, is_active=True).filter(Offer.valid_until >= date.today()).all()
    reviews = Review.query.filter_by(business_id=business.id, is_reported=False).order_by(Review.created_at.desc()).all()
    
    # User's own review if logged in
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(business_id=business.id, user_id=current_user.id).first()
        
    return render_template('business_details.html',
                           business=business,
                           products=products,
                           offers=active_offers,
                           reviews=reviews,
                           user_review=user_review)

@app.route('/compare-prices')
def compare_prices():
    """Local Price Comparison feature: Compare product prices across local stores."""
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    
    product_query = db.session.query(Product, Business).join(Business, Product.business_id == Business.id)\
                              .filter(Business.status == 'approved', Product.is_available == True)
                              
    if query:
        product_query = product_query.filter(Product.product_name.ilike(f"%{query}%"))
    if category_id:
        product_query = product_query.filter(Business.category_id == category_id)
        
    items = product_query.order_by(Product.product_name.asc(), Product.price.asc()).all()
    
    # Group by product name for easy comparison
    grouped_products = {}
    for product, biz in items:
        norm_name = product.product_name.strip()
        if norm_name not in grouped_products:
            grouped_products[norm_name] = []
        grouped_products[norm_name].append({
            'product': product,
            'business': biz
        })
        
    categories = Category.query.all()
    return render_template('price_comparison.html',
                           grouped_products=grouped_products,
                           categories=categories,
                           query=query,
                           selected_category=category_id)

@app.route('/offers')
def offers_page():
    """Browse all community discounts and offers."""
    offers = Offer.query.join(Business).filter(Business.status == 'approved', Offer.is_active == True, Offer.valid_until >= date.today())\
                 .order_by(Offer.discount_percent.desc()).all()
    return render_template('offers.html', offers=offers)

@app.route('/offer/<int:offer_id>/click')
def offer_click(offer_id):
    """Increment offer click counter and redirect to business."""
    offer = Offer.query.get_or_404(offer_id)
    offer.clicks_count = (offer.clicks_count or 0) + 1
    db.session.commit()
    flash(f"Coupon code '{offer.coupon_code}' copied! Show it at checkout.", 'success')
    return redirect(url_for('business_details', business_id=offer.business_id))

# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        elif current_user.is_owner():
            return redirect(url_for('owner_dashboard'))
        return redirect(url_for('customer_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('login.html')
                
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.full_name}!", 'success')
            
            # Role-based redirection
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            elif user.is_owner():
                return redirect(url_for('owner_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email address or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        full_name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        account_type = request.form.get('account_type', 'customer').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Normalize account type
        if 'owner' in account_type:
            role = 'owner'
        else:
            role = 'customer'

        # Validation
        if not full_name or not email or not phone or not password:
            flash('All required fields must be filled out.', 'danger')
            return render_template('register.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')
            
        if confirm_password and password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email address already exists. Please login.', 'warning')
            return redirect(url_for('login'))

        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            preferred_language=session.get('lang', 'en')
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Registration successful! Welcome to LocalBiz.', 'success')
        
        if new_user.is_owner():
            flash('Please register your business details to start promoting to customers.', 'info')
            return redirect(url_for('owner_add_business'))
        return redirect(url_for('explore'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

# ==============================================================================
# CUSTOMER MODULE ROUTES
# ==============================================================================

@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    my_reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    my_enquiries = Enquiry.query.filter_by(user_id=current_user.id).order_by(Enquiry.created_at.desc()).all()
    saved_searches = SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.searched_at.desc()).limit(10).all()
    return render_template('customer/dashboard.html',
                           reviews=my_reviews,
                           enquiries=my_enquiries,
                           searches=saved_searches)

@app.route('/business/<int:business_id>/review', methods=['POST'])
@login_required
def submit_review(business_id):
    business = Business.query.get_or_404(business_id)
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    if not rating or rating < 1 or rating > 5:
        flash('Please provide a valid rating between 1 and 5 stars.', 'danger')
        return redirect(url_for('business_details', business_id=business_id))
        
    if not comment:
        flash('Please write a short review comment explaining your experience.', 'danger')
        return redirect(url_for('business_details', business_id=business_id))
        
    existing_review = Review.query.filter_by(business_id=business.id, user_id=current_user.id).first()
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        existing_review.created_at = datetime.utcnow()
        flash('Your review has been updated!', 'success')
    else:
        new_review = Review(
            business_id=business.id,
            user_id=current_user.id,
            rating=rating,
            comment=comment
        )
        db.session.add(new_review)
        flash('Thank you! Your review has been submitted.', 'success')
        
    db.session.commit()
    business.update_rating()
    db.session.commit()
    
    return redirect(url_for('business_details', business_id=business_id))

@app.route('/business/<int:business_id>/enquiry', methods=['POST'])
def send_enquiry(business_id):
    business = Business.query.get_or_404(business_id)
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()
    
    if not name or not phone or not message:
        flash('Please fill in your name, phone number, and message.', 'danger')
        return redirect(url_for('business_details', business_id=business_id))
        
    enquiry = Enquiry(
        business_id=business.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        customer_name=name,
        customer_phone=phone,
        customer_email=email if email else None,
        message=message
    )
    db.session.add(enquiry)
    db.session.commit()
    
    flash('Your enquiry has been sent to the business owner. They will contact you shortly!', 'success')
    return redirect(url_for('business_details', business_id=business_id))

# ==============================================================================
# BUSINESS OWNER MODULE ROUTES
# ==============================================================================

@app.route('/owner-dashboard')
@owner_required
def owner_dashboard():
    # If admin viewing, allow picking owner or show admin's own businesses
    businesses = Business.query.filter_by(owner_id=current_user.id).all()
    biz_ids = [b.id for b in businesses]
    
    total_views = sum(b.view_count or 0 for b in businesses)
    total_products = Product.query.filter(Product.business_id.in_(biz_ids)).count() if biz_ids else 0
    total_enquiries = Enquiry.query.filter(Enquiry.business_id.in_(biz_ids)).count() if biz_ids else 0
    
    # Calculate average rating across owner's businesses
    rated_biz = [b for b in businesses if b.rating > 0]
    avg_rating = round(sum(b.rating for b in rated_biz) / len(rated_biz), 1) if rated_biz else 0.0
    
    recent_enquiries = Enquiry.query.filter(Enquiry.business_id.in_(biz_ids)).order_by(Enquiry.created_at.desc()).limit(5).all() if biz_ids else []
    recent_reviews = Review.query.filter(Review.business_id.in_(biz_ids)).order_by(Review.created_at.desc()).limit(5).all() if biz_ids else []
    
    return render_template('owner/dashboard.html',
                           businesses=businesses,
                           total_views=total_views,
                           total_products=total_products,
                           total_enquiries=total_enquiries,
                           avg_rating=avg_rating,
                           recent_enquiries=recent_enquiries,
                           recent_reviews=recent_reviews)

@app.route('/owner-add-business', methods=['GET', 'POST'])
@owner_required
def owner_add_business():
    categories = Category.query.all()
    if request.method == 'POST':
        name = request.form.get('business_name', '').strip()
        category_id = request.form.get('category_id', type=int)
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip() or 'Hiriyur'
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        website = request.form.get('website', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        lat = request.form.get('latitude', type=float) or 13.9450
        lng = request.form.get('longitude', type=float) or 76.6210
        
        if not name or not category_id or not address or not phone:
            flash('Business name, category, address, and phone number are required.', 'danger')
            return render_template('owner/add_business.html', categories=categories)
            
        new_biz = Business(
            owner_id=current_user.id,
            category_id=category_id,
            business_name=name,
            address=address,
            city=city,
            phone=phone,
            email=email,
            website=website,
            description=description,
            latitude=lat,
            longitude=lng,
            image_url=image_url if image_url else 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500&auto=format&fit=crop&q=60',
            status='approved' if current_user.is_admin() else 'pending'
        )
        db.session.add(new_biz)
        db.session.commit()
        
        flash('Business registered successfully! Admin will verify and activate your listing soon.', 'success')
        return redirect(url_for('owner_dashboard'))
        
    return render_template('owner/add_business.html', categories=categories)

@app.route('/owner/business/<int:business_id>/edit', methods=['GET', 'POST'])
@owner_required
def owner_edit_business(business_id):
    biz = Business.query.get_or_404(business_id)
    if biz.owner_id != current_user.id and not current_user.is_admin():
        abort(403)
        
    categories = Category.query.all()
    if request.method == 'POST':
        biz.business_name = request.form.get('business_name', '').strip()
        biz.category_id = request.form.get('category_id', type=int)
        biz.address = request.form.get('address', '').strip()
        biz.city = request.form.get('city', '').strip()
        biz.phone = request.form.get('phone', '').strip()
        biz.email = request.form.get('email', '').strip()
        biz.website = request.form.get('website', '').strip()
        biz.description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        if image_url:
            biz.image_url = image_url
            
        lat = request.form.get('latitude', type=float)
        lng = request.form.get('longitude', type=float)
        if lat is not None:
            biz.latitude = lat
        if lng is not None:
            biz.longitude = lng
            
        db.session.commit()
        flash('Business profile updated successfully.', 'success')
        return redirect(url_for('owner_dashboard'))
        
    return render_template('owner/edit_business.html', business=biz, categories=categories)

@app.route('/owner-add-product', methods=['GET', 'POST'])
@owner_required
def owner_add_product():
    businesses = Business.query.filter_by(owner_id=current_user.id).all()
    if not businesses:
        flash('Please register a business first before adding products.', 'warning')
        return redirect(url_for('owner_add_business'))
        
    if request.method == 'POST':
        business_id = request.form.get('business_id', type=int)
        product_name = request.form.get('product_name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        unit = request.form.get('unit', 'piece').strip()
        image_url = request.form.get('image_url', '').strip()
        
        # Verify ownership
        biz = db.session.get(Business, business_id)
        if not biz or (biz.owner_id != current_user.id and not current_user.is_admin()):
            flash('Invalid business selected.', 'danger')
            return redirect(url_for('owner_add_product'))
            
        if not product_name or price is None:
            flash('Product name and valid price are required.', 'danger')
            return render_template('owner/add_product.html', businesses=businesses)
            
        product = Product(
            business_id=business_id,
            product_name=product_name,
            description=description,
            price=price,
            unit=unit,
            image_url=image_url if image_url else 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60'
        )
        db.session.add(product)
        db.session.commit()
        
        flash(f"Product '{product_name}' added successfully!", 'success')
        return redirect(url_for('owner_products'))
        
    return render_template('owner/add_product.html', businesses=businesses)

@app.route('/owner/products')
@owner_required
def owner_products():
    businesses = Business.query.filter_by(owner_id=current_user.id).all()
    biz_ids = [b.id for b in businesses]
    products = Product.query.filter(Product.business_id.in_(biz_ids)).all() if biz_ids else []
    return render_template('owner/products.html', products=products, businesses=businesses)

@app.route('/owner/product/<int:product_id>/delete', methods=['POST'])
@owner_required
def owner_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.business.owner_id != current_user.id and not current_user.is_admin():
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully.', 'info')
    return redirect(url_for('owner_products'))

@app.route('/owner/offers', methods=['GET', 'POST'])
@owner_required
def owner_offers():
    businesses = Business.query.filter_by(owner_id=current_user.id).all()
    biz_ids = [b.id for b in businesses]
    
    if request.method == 'POST':
        business_id = request.form.get('business_id', type=int)
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        discount_percent = request.form.get('discount_percent', type=float) or 0.0
        coupon_code = request.form.get('coupon_code', '').strip().upper()
        valid_until_str = request.form.get('valid_until', '').strip()
        
        if not title or not valid_until_str:
            flash('Offer title and expiration date are required.', 'danger')
        else:
            valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d').date()
            offer = Offer(
                business_id=business_id,
                title=title,
                description=description,
                discount_percent=discount_percent,
                coupon_code=coupon_code if coupon_code else None,
                valid_until=valid_until
            )
            db.session.add(offer)
            db.session.commit()
            flash('Special offer published successfully!', 'success')
            return redirect(url_for('owner_offers'))
            
    offers = Offer.query.filter(Offer.business_id.in_(biz_ids)).order_by(Offer.created_at.desc()).all() if biz_ids else []
    return render_template('owner/offers.html', offers=offers, businesses=businesses)

@app.route('/owner/offer/<int:offer_id>/delete', methods=['POST'])
@owner_required
def owner_delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    if offer.business.owner_id != current_user.id and not current_user.is_admin():
        abort(403)
    db.session.delete(offer)
    db.session.commit()
    flash('Offer removed successfully.', 'info')
    return redirect(url_for('owner_offers'))

@app.route('/owner/enquiries')
@owner_required
def owner_enquiries():
    businesses = Business.query.filter_by(owner_id=current_user.id).all()
    biz_ids = [b.id for b in businesses]
    enquiries = Enquiry.query.filter(Enquiry.business_id.in_(biz_ids)).order_by(Enquiry.created_at.desc()).all() if biz_ids else []
    return render_template('owner/enquiries.html', enquiries=enquiries)

@app.route('/owner/enquiry/<int:enquiry_id>/reply', methods=['POST'])
@owner_required
def owner_reply_enquiry(enquiry_id):
    enquiry = Enquiry.query.get_or_404(enquiry_id)
    if enquiry.business.owner_id != current_user.id and not current_user.is_admin():
        abort(403)
    reply = request.form.get('reply_message', '').strip()
    if reply:
        enquiry.reply_message = reply
        enquiry.status = 'replied'
        db.session.commit()
        flash('Reply submitted to customer enquiry.', 'success')
    return redirect(url_for('owner_enquiries'))

@app.route('/owner/reviews')
@owner_required
def owner_reviews():
    businesses = Business.query.filter_by(owner_id=current_user.id).all()
    biz_ids = [b.id for b in businesses]
    reviews = Review.query.filter(Review.business_id.in_(biz_ids)).order_by(Review.created_at.desc()).all() if biz_ids else []
    return render_template('owner/reviews.html', reviews=reviews)

@app.route('/owner/review/<int:review_id>/report', methods=['POST'])
@owner_required
def owner_report_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.business.owner_id != current_user.id and not current_user.is_admin():
        abort(403)
    reason = request.form.get('reason', 'Inappropriate or abusive language').strip()
    review.is_reported = True
    review.report_reason = reason
    db.session.commit()
    review.business.update_rating()
    db.session.commit()
    flash('Review reported to administrator for moderation.', 'info')
    return redirect(url_for('owner_reviews'))

@app.route('/owner-analytics')
@owner_required
def owner_analytics():
    """Detailed analytics dashboard for business owners."""
    businesses = Business.query.filter_by(owner_id=current_user.id).all()
    biz_ids = [b.id for b in businesses]
    
    total_views = sum(b.view_count or 0 for b in businesses)
    total_enquiries = Enquiry.query.filter(Enquiry.business_id.in_(biz_ids)).count() if biz_ids else 0
    total_products = Product.query.filter(Product.business_id.in_(biz_ids)).count() if biz_ids else 0
    total_reviews = Review.query.filter(Review.business_id.in_(biz_ids)).count() if biz_ids else 0
    
    # Daily views for the last 7 days
    today = date.today()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    days_labels = [d.strftime('%a, %d %b') for d in days]
    views_by_day = []
    
    for d in days:
        cnt = db.session.query(func.count(BusinessView.id))\
                        .filter(BusinessView.business_id.in_(biz_ids))\
                        .filter(func.date(BusinessView.viewed_at) == d).scalar() if biz_ids else 0
        views_by_day.append(cnt)
        
    # Offer performance
    offers = Offer.query.filter(Offer.business_id.in_(biz_ids)).all() if biz_ids else []
    
    return render_template('owner/analytics.html',
                           businesses=businesses,
                           total_views=total_views,
                           total_enquiries=total_enquiries,
                           total_products=total_products,
                           total_reviews=total_reviews,
                           days_labels=days_labels,
                           views_by_day=views_by_day,
                           offers=offers)

# ==============================================================================
# ADMIN MODULE ROUTES
# ==============================================================================

@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_customers = User.query.filter_by(role='customer').count()
    total_owners = User.query.filter_by(role='owner').count()
    total_businesses = Business.query.count()
    pending_businesses = Business.query.filter_by(status='pending').all()
    reported_reviews = Review.query.filter_by(is_reported=True).all()
    categories = Category.query.all()
    
    # Recent portal activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_searches = SearchHistory.query.order_by(SearchHistory.searched_at.desc()).limit(8).all()
    
    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_customers=total_customers,
                           total_owners=total_owners,
                           total_businesses=total_businesses,
                           pending_businesses=pending_businesses,
                           reported_reviews=reported_reviews,
                           categories=categories,
                           recent_users=recent_users,
                           recent_searches=recent_searches)

@app.route('/admin/businesses')
@admin_required
def admin_businesses():
    status = request.args.get('status', 'all')
    if status != 'all':
        businesses = Business.query.filter_by(status=status).order_by(Business.created_at.desc()).all()
    else:
        businesses = Business.query.order_by(Business.created_at.desc()).all()
    return render_template('admin/businesses.html', businesses=businesses, current_status=status)

@app.route('/admin/business/<int:business_id>/status', methods=['POST'])
@admin_required
def admin_set_business_status(business_id):
    biz = Business.query.get_or_404(business_id)
    new_status = request.form.get('status')
    if new_status in ['approved', 'rejected', 'pending']:
        biz.status = new_status
        db.session.commit()
        flash(f"Business '{biz.business_name}' status updated to {new_status}.", 'success')
    return redirect(request.referrer or url_for('admin_businesses'))

@app.route('/admin/users')
@admin_required
def admin_users():
    role_filter = request.args.get('role', 'all')
    if role_filter != 'all':
        users = User.query.filter_by(role=role_filter).order_by(User.created_at.desc()).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users, current_role=role_filter)

@app.route('/admin/user/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own admin account.', 'danger')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f"User '{user.full_name}' status toggled to {'Active' if user.is_active else 'Deactivated'}.", 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        kannada_name = request.form.get('kannada_name', '').strip()
        icon = request.form.get('icon', '🏪').strip()
        description = request.form.get('description', '').strip()
        
        if not name or not kannada_name:
            flash('English and Kannada names are required.', 'danger')
        else:
            existing_cat = Category.query.filter_by(name=name).first()
            if existing_cat:
                flash(f"Category '{name}' already exists.", 'warning')
            else:
                cat = Category(name=name, kannada_name=kannada_name, icon=icon, description=description)
                db.session.add(cat)
                db.session.commit()
                flash('Category added successfully!', 'success')
            return redirect(url_for('admin_categories'))
            
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    reported_reviews = Review.query.filter_by(is_reported=True).all()
    all_reviews = Review.query.order_by(Review.created_at.desc()).limit(30).all()
    return render_template('admin/reviews.html', reported_reviews=reported_reviews, all_reviews=all_reviews)

@app.route('/admin/review/<int:review_id>/resolve', methods=['POST'])
@admin_required
def admin_resolve_review(review_id):
    action = request.form.get('action') # 'dismiss' or 'delete'
    review = Review.query.get_or_404(review_id)
    biz = review.business
    
    if action == 'delete':
        db.session.delete(review)
        db.session.commit()
        biz.update_rating()
        db.session.commit()
        flash('Reported review deleted permanently.', 'success')
    else:
        review.is_reported = False
        review.report_reason = None
        db.session.commit()
        biz.update_rating()
        db.session.commit()
        flash('Report dismissed. Review kept active.', 'info')
        
    return redirect(url_for('admin_reviews'))

# ==============================================================================
# MARKET ANALYTICS MODULE
# ==============================================================================

@app.route('/analytics')
def analytics():
    """Portal-wide market analytics dashboard using actual database data."""
    total_businesses = Business.query.filter_by(status='approved').count()
    total_customers = User.query.filter_by(role='customer').count()
    total_owners = User.query.filter_by(role='owner').count()
    total_views = db.session.query(func.coalesce(func.sum(Business.view_count), 0)).scalar()
    total_enquiries = Enquiry.query.count()
    
    # 1. Most popular business categories by view count & business count
    category_stats = db.session.query(
        Category.name,
        Category.kannada_name,
        Category.icon,
        func.count(Business.id).label('biz_count'),
        func.coalesce(func.sum(Business.view_count), 0).label('total_views')
    ).outerjoin(Business, (Business.category_id == Category.id) & (Business.status == 'approved'))\
     .group_by(Category.id)\
     .order_by(desc('total_views'), desc('biz_count')).all()
     
    # 2. Most viewed businesses
    top_businesses = Business.query.filter_by(status='approved')\
                           .order_by(Business.view_count.desc(), Business.rating.desc())\
                           .limit(5).all()
                           
    # 3. Customer search trends (top keywords)
    search_trends = db.session.query(
        SearchHistory.search_query, func.count(SearchHistory.id).label('count')
    ).filter(SearchHistory.search_query.isnot(None))\
     .group_by(SearchHistory.search_query)\
     .order_by(desc('count'))\
     .limit(6).all()
     
    # 4. Profile views trend over the last 7 days
    today = date.today()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    days_labels = [d.strftime('%b %d') for d in days]
    views_trend = []
    for d in days:
        c = db.session.query(func.count(BusinessView.id))\
                      .filter(func.date(BusinessView.viewed_at) == d).scalar()
        views_trend.append(c)
        
    # 5. Enquiry statistics breakdown
    enquiry_stats = {
        'total': total_enquiries,
        'new': Enquiry.query.filter_by(status='new').count(),
        'replied': Enquiry.query.filter_by(status='replied').count(),
        'read': Enquiry.query.filter_by(status='read').count()
    }
    
    # 6. Promotion performance
    top_offers = Offer.query.filter_by(is_active=True).order_by(Offer.clicks_count.desc()).limit(5).all()
    
    return render_template('analytics.html',
                           total_businesses=total_businesses,
                           total_customers=total_customers,
                           total_owners=total_owners,
                           total_views=total_views,
                           total_enquiries=total_enquiries,
                           category_stats=category_stats,
                           top_businesses=top_businesses,
                           search_trends=search_trends,
                           days_labels=days_labels,
                           views_trend=views_trend,
                           enquiry_stats=enquiry_stats,
                           top_offers=top_offers)

# API endpoint for asynchronous chart updates
@app.route('/api/analytics-data')
def api_analytics_data():
    category_stats = db.session.query(
        Category.name, func.coalesce(func.sum(Business.view_count), 0).label('views')
    ).outerjoin(Business, (Business.category_id == Category.id) & (Business.status == 'approved'))\
     .group_by(Category.id).all()
     
    labels = [c[0] for c in category_stats]
    views = [c[1] for c in category_stats]
    return jsonify({'labels': labels, 'views': views})

# ==============================================================================
# AI CHATBOT & LOCATION TRACKING API ENDPOINTS
# ==============================================================================

@app.route('/api/ai-chat', methods=['POST'])
def api_ai_chat():
    """Context-aware local business AI assistant endpoint."""
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    lang = data.get('lang', session.get('lang', 'en'))
    user_lat = data.get('lat')
    user_lng = data.get('lng')
    
    response = generate_ai_response(message, lang=lang, user_lat=user_lat, user_lng=user_lng)
    return jsonify(response)

@app.route('/api/nearby-businesses')
def api_nearby_businesses():
    """Live location tracking API calculating distances to all local shops."""
    try:
        user_lat = float(request.args.get('lat'))
        user_lng = float(request.args.get('lng'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Valid lat and lng required'}), 400
        
    radius = request.args.get('radius', default=25.0, type=float)
    category_id = request.args.get('category', type=int)
    
    query = Business.query.filter_by(status='approved')
    if category_id:
        query = query.filter_by(category_id=category_id)
        
    businesses = query.all()
    results = []
    for b in businesses:
        dist = b.distance_from(user_lat, user_lng)
        if dist is not None and dist <= radius:
            results.append({
                'id': b.id,
                'name': b.business_name,
                'category': b.category.name,
                'category_icon': b.category.icon,
                'city': b.city,
                'address': b.address,
                'phone': b.phone,
                'rating': b.rating,
                'total_reviews': b.total_reviews,
                'distance_km': dist,
                'image_url': b.image_url,
                'url': url_for('business_details', business_id=b.id),
                'directions_url': f"https://www.google.com/maps/dir/?api=1&destination={b.latitude},{b.longitude}"
            })
            
    results.sort(key=lambda x: x['distance_km'])
    return jsonify({'count': len(results), 'businesses': results})

# ==============================================================================
# APPLICATION BOOTSTRAP
# ==============================================================================

if __name__ == '__main__':
    with app.app_context():
        # Ensure database tables exist and seed demo records
        seed_database(app)
    app.run(debug=True, port=5000)
