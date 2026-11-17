"""
Comprehensive Automated Test Suite for LocalBiz
Tests every route, module, authentication, RBAC, reviews, enquiries, and analytics.
"""
import unittest
from app import app
from models import db, User, Business, Category, Product, Offer, Review, Enquiry
from init_db import seed_database

class LocalBizTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        with self.app.app_context():
            seed_database(self.app)

    def login(self, email, password):
        return self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    # 1. Public Routes
    def test_01_public_routes(self):
        print("\n--- Testing Public Routes ---")
        routes = ['/', '/explore', '/compare-prices', '/offers', '/analytics', '/login', '/register']
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, f"Route {route} failed with status {response.status_code}")
            print(f"  [PASS] GET {route} -> 200 OK")

    # 2. Language Switcher
    def test_02_language_switcher(self):
        print("\n--- Testing Bilingual Kannada & English Support ---")
        res_kn = self.client.get('/set-language/kn', follow_redirects=True)
        self.assertEqual(res_kn.status_code, 200)
        self.assertIn('ಸ್ಥಳೀಯ'.encode('utf-8'), res_kn.data)
        print("  [PASS] Kannada language switched and verified")

        res_en = self.client.get('/set-language/en', follow_redirects=True)
        self.assertEqual(res_en.status_code, 200)
        self.assertIn(b'Support Local Businesses', res_en.data)
        print("  [PASS] English language switched and verified")

    # 3. Explore & Smart Search Filtering
    def test_03_explore_filters(self):
        print("\n--- Testing Smart Local Business Finder & Search ---")
        # Search keyword
        res_search = self.client.get('/explore?q=food')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'Local Food Corner', res_search.data)
        print("  [PASS] Keyword search ('food')")

        # Category filter
        res_cat = self.client.get('/explore?category=1')
        self.assertEqual(res_cat.status_code, 200)
        print("  [PASS] Category filter")

        # City filter
        res_city = self.client.get('/explore?city=Hiriyur')
        self.assertEqual(res_city.status_code, 200)
        print("  [PASS] City filter ('Hiriyur')")

    # 4. Business Details & Enquiry Submission
    def test_04_business_details_and_enquiry(self):
        print("\n--- Testing Business Details & Customer Enquiry ---")
        res = self.client.get('/business/1')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Local Food Corner', res.data)
        print("  [PASS] GET /business/1 details page")

        # Send enquiry
        enq_res = self.client.post('/business/1/enquiry', data=dict(
            name='Test Customer',
            phone='9876543210',
            email='test@example.com',
            message='Is catering available for tomorrow?'
        ), follow_redirects=True)
        self.assertEqual(enq_res.status_code, 200)
        with self.app.app_context():
            enq = Enquiry.query.filter_by(customer_name='Test Customer').first()
            self.assertIsNotNone(enq)
            self.assertEqual(enq.business_id, 1)
        print("  [PASS] Customer enquiry submitted & saved to database")

    # 5. Customer Authentication & Review Submission
    def test_05_customer_review(self):
        print("\n--- Testing Customer Review & Rating ---")
        login_res = self.login('customer@localbiz.com', 'Customer@123')
        self.assertEqual(login_res.status_code, 200)
        print("  [PASS] Customer logged in")

        # Submit review
        rev_res = self.client.post('/business/1/review', data=dict(
            rating=5,
            comment='Outstanding authentic taste and prompt service!'
        ), follow_redirects=True)
        self.assertEqual(rev_res.status_code, 200)
        with self.app.app_context():
            biz = db.session.get(Business, 1)
            self.assertGreater(biz.rating, 0)
        print("  [PASS] Customer review submitted & business rating updated")

        # Check customer dashboard
        dash_res = self.client.get('/customer/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b'My Enquiries', dash_res.data)
        print("  [PASS] Customer dashboard accessed")
        self.logout()

    # 6. Business Owner Module
    def test_06_business_owner_module(self):
        print("\n--- Testing Business Owner Module ---")
        login_res = self.login('owner@localbiz.com', 'Owner@123')
        self.assertEqual(login_res.status_code, 200)
        print("  [PASS] Owner logged in")

        # Owner dashboard
        dash_res = self.client.get('/owner-dashboard')
        self.assertEqual(dash_res.status_code, 200)
        print("  [PASS] Owner dashboard -> 200 OK")

        # Add product
        with self.app.app_context():
            biz = Business.query.filter_by(owner_id=User.query.filter_by(email='owner@localbiz.com').first().id).first()
            biz_id = biz.id

        prod_res = self.client.post('/owner-add-product', data=dict(
            business_id=biz_id,
            product_name='Test Mysore Pak Special',
            description='Traditional ghee sweet melt in mouth',
            price=250.00,
            unit='box'
        ), follow_redirects=True)
        self.assertEqual(prod_res.status_code, 200)
        with self.app.app_context():
            p = Product.query.filter_by(product_name='Test Mysore Pak Special').first()
            self.assertIsNotNone(p)
        print("  [PASS] Product added by owner")

        # Add special offer
        offer_res = self.client.post('/owner/offers', data=dict(
            business_id=biz_id,
            title='Mega Flash 25% OFF',
            discount_percent=25.0,
            coupon_code='MEGA25',
            valid_until='2026-12-31',
            description='Applicable on all items'
        ), follow_redirects=True)
        self.assertEqual(offer_res.status_code, 200)
        with self.app.app_context():
            o = Offer.query.filter_by(coupon_code='MEGA25').first()
            self.assertIsNotNone(o)
        print("  [PASS] Special offer published by owner")

        # Owner analytics
        ana_res = self.client.get('/owner-analytics')
        self.assertEqual(ana_res.status_code, 200)
        print("  [PASS] Owner analytics -> 200 OK")
        self.logout()

    # 7. Admin Module
    def test_07_admin_module(self):
        print("\n--- Testing Administrator Control Center ---")
        login_res = self.login('admin@localbiz.com', 'Admin@123')
        self.assertEqual(login_res.status_code, 200)
        print("  [PASS] Admin logged in")

        # Admin dashboard
        dash_res = self.client.get('/admin-dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b'Administrator Control Center', dash_res.data)
        print("  [PASS] Admin dashboard -> 200 OK")

        # Verify / Approve pending business
        with self.app.app_context():
            pending_biz = Business.query.filter_by(status='pending').first()
            if pending_biz:
                pending_id = pending_biz.id
                appr_res = self.client.post(f'/admin/business/{pending_id}/status', data=dict(
                    status='approved'
                ), follow_redirects=True)
                self.assertEqual(appr_res.status_code, 200)
                updated_biz = db.session.get(Business, pending_id)
                self.assertEqual(updated_biz.status, 'approved')
                print(f"  [PASS] Admin verified & approved business id={pending_id}")

        # Add category
        cat_res = self.client.post('/admin/categories', data=dict(
            name='Auto & Transport',
            kannada_name='ವಾಹನ ಮತ್ತು ಸಾರಿಗೆ',
            icon='🚗',
            description='Vehicle repairs, auto spares, and local transport'
        ), follow_redirects=True)
        self.assertEqual(cat_res.status_code, 200)
        with self.app.app_context():
            c = Category.query.filter_by(name='Auto & Transport').first()
            self.assertIsNotNone(c)
        print("  [PASS] Category created by admin")

        # Analytics API
        api_res = self.client.get('/api/analytics-data')
        self.assertEqual(api_res.status_code, 200)
        self.assertIn('labels', api_res.get_json())
        print("  [PASS] Analytics JSON API -> 200 OK")
        self.logout()

    # 8. Role-Based Access Control
    def test_08_rbac_protection(self):
        print("\n--- Testing Role-Based Access Control (RBAC) ---")
        # Customer trying to access Admin Dashboard
        self.login('customer@localbiz.com', 'Customer@123')
        admin_res = self.client.get('/admin-dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', admin_res.data)
        print("  [PASS] Customer blocked from admin dashboard")

        # Customer trying to access Owner Dashboard
        owner_res = self.client.get('/owner-dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', owner_res.data)
        print("  [PASS] Customer blocked from owner dashboard")
        self.logout()

        # Unauthenticated user access
        unauth_res = self.client.get('/owner-dashboard', follow_redirects=True)
        self.assertIn(b'Please log in', unauth_res.data)
        print("  [PASS] Unauthenticated user redirected to login")

    # 9. AI Chatbot
    def test_09_ai_chatbot(self):
        print("\n--- Testing LocalBiz AI Chatbot (/api/ai-chat) ---")
        # Test greeting
        res_greet = self.client.post('/api/ai-chat', json={'message': 'hello'})
        self.assertEqual(res_greet.status_code, 200)
        data = res_greet.get_json()
        self.assertIn('LocalBiz AI Assistant', data['reply'])
        print("  [PASS] AI Chatbot greeting response")

        # Test product price search
        res_prod = self.client.post('/api/ai-chat', json={'message': 'price of charger'})
        self.assertEqual(res_prod.status_code, 200)
        prod_data = res_prod.get_json()
        self.assertIn('₹', prod_data['reply'])
        print("  [PASS] AI Chatbot live product price comparison")

        # Test Kannada query
        res_kn = self.client.post('/api/ai-chat', json={'message': 'ನಮಸ್ಕಾರ', 'lang': 'kn'})
        self.assertEqual(res_kn.status_code, 200)
        kn_data = res_kn.get_json()
        self.assertIn('ಸಹಾಯಕ', kn_data['reply'])
        print("  [PASS] AI Chatbot bilingual Kannada response")

    # 10. Track Location & Nearby Businesses Tool
    def test_10_track_location(self):
        print("\n--- Testing Track Location & Near Me Tool ---")
        # Test nearby businesses API with Hiriyur coordinates
        res_nearby = self.client.get('/api/nearby-businesses?lat=13.9450&lng=76.6210&radius=10')
        self.assertEqual(res_nearby.status_code, 200)
        data = res_nearby.get_json()
        self.assertGreater(data['count'], 0)
        self.assertIn('distance_km', data['businesses'][0])
        print(f"  [PASS] Found {data['count']} businesses within 10 km of Hiriyur")

        # Test Explore route with user location & sort=nearest
        res_explore = self.client.get('/explore?lat=13.9450&lng=76.6210&sort=nearest')
        self.assertEqual(res_explore.status_code, 200)
        self.assertIn(b'km away', res_explore.data)
        print("  [PASS] Explore page rendered live distance badges")

    # 11. Expanded Shops Verification
    def test_11_expanded_shops(self):
        print("\n--- Testing Expanded Diverse Shops ---")
        with self.app.app_context():
            biz_count = Business.query.count()
            prod_count = Product.query.count()
            self.assertGreaterEqual(biz_count, 10)
            self.assertGreaterEqual(prod_count, 20)
            print(f"  [PASS] Verified {biz_count} shops and {prod_count} catalog products in database")

if __name__ == '__main__':
    unittest.main()
