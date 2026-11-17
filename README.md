# LOCAL BUSINESS PROMOTION AND MARKET ANALYTICS PORTAL (LocalBiz)

**A Full-Stack Community Web Application**  
*Developed with Python, Flask, MySQL, Bootstrap 5, JavaScript, and Chart.js*

---

## 1. Project Overview

**LocalBiz** connects neighborhood business owners with customers in local towns (such as Hiriyur, Chitradurga, and surrounding regions). The platform empowers small businesses to establish a digital presence, list products and services, publish promotional discount coupons, communicate directly with customers via enquiries, and analyze market demand through data-driven analytics.

### Key Objectives
1. **Support Local Commerce:** Help brick-and-mortar neighborhood stores compete with e-commerce giants.
2. **Transparent Price Discovery:** Enable consumers to compare local prices across registered stores.
3. **Bilingual Accessibility:** Provide native Kannada (ಕನ್ನಡ) and English language support.
4. **Market Analytics:** Provide real database metrics on category trends, customer search volume, and promotional performance.

---

## 2. Technologies & Architecture

- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4
- **Backend:** Python 3.14, Flask 3.1.3, Flask-Login 0.6.3, Flask-SQLAlchemy 3.1.1, Werkzeug 3.1.9
- **Database:** MySQL (Primary, PyMySQL connector) with automatic zero-configuration SQLite fallback (`localbiz.db`) for immediate testing
- **Testing:** Python `unittest` suite (`test_app.py`)

---

## 3. Project Directory Structure

```
LOCAL_BUSINESS_PORTAL/
├── app.py                     # Main Flask application with 37 routes & controllers
├── config.py                  # Database, session, and application configuration
├── models.py                  # 9 SQLAlchemy relational database models
├── translations.py            # Bilingual dictionary (Kannada & English)
├── init_db.py                 # Database table creation and realistic sample data seeder
├── test_app.py                # Comprehensive automated test suite (8 test suites)
├── requirements.txt           # Python library dependencies
├── README.md                  # Project documentation & viva guide
├── database/
│   └── schema.sql             # Complete MySQL DDL script with 9 normalized tables
├── static/
│   ├── css/
│   │   ├── style.css          # Main modern stylesheet (Bootstrap 5 theme & cards)
│   │   └── auth.css           # Auth forms styling
│   ├── js/
│   │   └── scripts.js         # Interactive JS (coupon copying, star ratings, alerts)
│   ├── images/                # Static image assets
│   └── uploads/               # User-uploaded business and product imagery
└── templates/
    ├── base.html              # Core layout (bilingual switcher, responsive navbar, footer)
    ├── index.html             # Homepage (hero search, categories, featured shops, offers)
    ├── explore.html           # Smart Local Business Finder (multi-filter & sorting)
    ├── business_details.html  # Storefront page (catalog, reviews, offers, enquiry modal)
    ├── price_comparison.html  # Local Price Comparison tool across stores
    ├── offers.html            # Community discounts and coupon code explorer
    ├── analytics.html         # Portal-wide market analytics dashboard (Chart.js)
    ├── login.html             # Secure user authentication with demo account quick-fill
    ├── register.html          # Registration for Customers and Business Owners
    ├── customer/
    │   └── dashboard.html     # Customer account (sent enquiries, reviews, search history)
    ├── owner/
    │   ├── dashboard.html     # Business owner overview (stats, shop profiles, enquiries)
    │   ├── add_business.html  # Business listing registration form
    │   ├── edit_business.html # Business profile editor
    │   ├── add_product.html   # Product/service catalog creation
    │   ├── products.html      # Product inventory management
    │   ├── offers.html        # Special discount publisher and click tracker
    │   ├── enquiries.html     # Customer enquiry inbox with response messaging
    │   ├── reviews.html       # Customer ratings & review reporting
    │   └── analytics.html     # Store-level views, impressions & conversion charts
    └── admin/
        ├── dashboard.html     # Admin command center (summary stats, pending queue)
        ├── businesses.html    # Verify or reject business registrations
        ├── users.html         # User account management & deactivation
        ├── categories.html    # Bilingual category manager (Kannada + English)
        └── reviews.html       # Review moderation for reported customer feedback
```

---

## 4. Database Setup (MySQL)

### Database Details:
- **Database Name:** `localbiz`
- **Tables:** 
  1. `users` (id, full_name, email, phone, password_hash, role, preferred_language, is_active, created_at)
  2. `categories` (id, name, kannada_name, icon, description, created_at)
  3. `businesses` (id, owner_id, category_id, business_name, description, address, city, phone, email, website, status, rating, total_reviews, view_count, image_url)
  4. `products` (id, business_id, product_name, description, price, unit, image_url, is_available)
  5. `offers` (id, business_id, title, description, discount_percent, coupon_code, valid_until, clicks_count, is_active)
  6. `reviews` (id, business_id, user_id, rating, comment, is_reported, report_reason)
  7. `enquiries` (id, business_id, user_id, customer_name, customer_phone, customer_email, message, status, reply_message)
  8. `business_views` (id, business_id, ip_address, user_id, viewed_at)
  9. `search_history` (id, user_id, search_query, category_filter, location_filter, searched_at)

### Importing to MySQL:
```bash
# Log in to MySQL CLI and run the script
mysql -u root -p < database/schema.sql
```

### Automatic Development Fallback:
If MySQL server is not active on port 3306, `app.py` automatically detects this and falls back to a local SQLite database (`localbiz.db`) with identical schema and full realistic sample data, ensuring the application runs out-of-the-box in any environment.

---

## 5. Demo Accounts for Demonstration

| Role | Email Address | Password | Permissions & Dashboard |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@localbiz.com` | `Admin@123` | Full portal governance, verify/reject businesses, user management, category CRUD, review moderation, portal analytics |
| **Business Owner** | `owner@localbiz.com` | `Owner@123` | Store dashboard, add/edit business, manage products, publish offers, reply to customer enquiries, view store analytics |
| **Customer** | `customer@localbiz.com` | `Customer@123` | Browse & search shops, compare prices, write ratings/reviews, send enquiries, track responses |

---

## 6. Unique Features Implemented

1. **Smart Local Business Finder:** Multi-criteria search matching keywords across business name, category, town/city, and minimum customer rating.
2. **Trending Business Categories:** Dynamically calculated popularity rankings based on actual store count and customer view logs.
3. **Local Price Comparison Tool:** Side-by-side product pricing table across multiple neighborhood stores to highlight best deals.
4. **Kannada and English Bilingual Support (ದ್ವಿಭಾಷಾ ಬೆಂಬಲ):** Real-time language toggle switching the entire UI between English and Kannada with session persistence.
5. **Business Promotion Performance Analytics:** Owner analytics showing daily storefront impressions, customer inquiries, and discount coupon click-through conversion.
6. **Customer Review & Rating System:** Verified 1-5 star ratings with dynamic average score recalculation and owner reporting mechanism.
7. **Location-based Business Discovery:** Direct town and locality filtering (e.g. Hiriyur, Chitradurga, Bengaluru).
8. **Special Offers & Discount Management:** Owner coupon manager with percentage discounts, validity countdowns, and one-click copyable promo codes.

---

## 7. How to Run the Project

### Step 1: Open Terminal in Project Folder
```bash
cd "C:\Users\prave\OneDrive\Documents\LOCAL_BUSINESS_PORTAL"
```

### Step 2: Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Run the Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

### Step 4: Run the Automated Test Suite
```bash
python -m unittest test_app.py
```
All 8 test suites will execute and verify public routes, authentication, RBAC, reviews, owner actions, admin actions, and analytics.
