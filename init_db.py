import os
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
from models import db, User, Category, Business, Product, Offer, Review, Enquiry, BusinessView, SearchHistory

def seed_database(app, force_reseed=False):
    """Populate database with default categories, initial demo users, and realistic local data."""
    with app.app_context():
        if force_reseed:
            db.drop_all()
        db.create_all()
        
        # 1. Seed Categories if empty
        if Category.query.count() == 0:
            categories = [
                Category(name='Restaurants & Cafes', kannada_name='ರೆಸ್ಟೋರೆಂಟ್‌ಗಳು ಮತ್ತು ಕೆಫೆಗಳು', icon='🍔', description='Local eateries, traditional cuisine, cafes, and bakeries'),
                Category(name='Mobile & Electronics', kannada_name='ಮೊಬೈಲ್ ಮತ್ತು ಎಲೆಕ್ಟ್ರಾನಿಕ್ಸ್', icon='📱', description='Smartphones, gadgets, repairs, and electronic accessories'),
                Category(name='Clothing & Fashion', kannada_name='ಬಟ್ಟೆ ಮತ್ತು ಫ್ಯಾಷನ್', icon='👕', description='Ethnic wear, western clothes, boutiques, and footwear'),
                Category(name='Grocery & Supermarket', kannada_name='ದಿನಸಿ ಮತ್ತು ಸೂಪರ್‌ಮಾರ್ಕೆಟ್', icon='🛒', description='Daily essentials, fresh vegetables, pulses, and spices'),
                Category(name='Salons & Personal Care', kannada_name='ಸಲೂನ್‌ಗಳು ಮತ್ತು ಸೌಂದರ್ಯ', icon='💇', description='Hair dressing, spa, grooming, and skincare centers'),
                Category(name='Health & Pharmacy', kannada_name='ಆರೋಗ್ಯ ಮತ್ತು ಔಷಧಾಲಯ', icon='💊', description='Clinics, pharmacies, medical supplies, and ayurveda'),
                Category(name='Books & Education', kannada_name='ಪುಸ್ತಕಗಳು ಮತ್ತು ಶಿಕ್ಷಣ', icon='📚', description='School & college books, stationery, printing, and study supplies'),
                Category(name='Auto & Transport', kannada_name='ವಾಹನ ಮತ್ತು ಸಾರಿಗೆ', icon='🚗', description='Bike & car repairs, engine oil, spare parts, and tyre care'),
                Category(name='Electricals & Hardware', kannada_name='ಎಲೆಕ್ಟ್ರಿಕಲ್ ಮತ್ತು ಹಾರ್ಡ್‌ವೇರ್', icon='⚡', description='Fans, LED lights, plumbing fixtures, cables, and tools'),
                Category(name='Jewelry & Watches', kannada_name='ಚಿನ್ನ, ಬೆಳ್ಳಿ ಮತ್ತು ಕೈಗಡಿಯಾರಗಳು', icon='💎', description='Traditional silver articles, gift items, watches, and ornaments')
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("Categories seeded successfully.")
            
        # 2. Seed Default Users if empty
        admin = User.query.filter_by(email='admin@localbiz.com').first()
        if not admin:
            admin = User(
                full_name='Portal Administrator',
                email='admin@localbiz.com',
                phone='9876543210',
                role='admin',
                password_hash=generate_password_hash('Admin@123')
            )
            db.session.add(admin)
            
        owner = User.query.filter_by(email='owner@localbiz.com').first()
        if not owner:
            owner = User(
                full_name='Ramesh Kumar',
                email='owner@localbiz.com',
                phone='9845012345',
                role='owner',
                password_hash=generate_password_hash('Owner@123')
            )
            db.session.add(owner)
            
        owner2 = User.query.filter_by(email='suresh@localbiz.com').first()
        if not owner2:
            owner2 = User(
                full_name='Suresh Gowda',
                email='suresh@localbiz.com',
                phone='9900112233',
                role='owner',
                password_hash=generate_password_hash('Owner@123')
            )
            db.session.add(owner2)

        owner3 = User.query.filter_by(email='manjunath@localbiz.com').first()
        if not owner3:
            owner3 = User(
                full_name='Manjunath Shettar',
                email='manjunath@localbiz.com',
                phone='9880123456',
                role='owner',
                password_hash=generate_password_hash('Owner@123')
            )
            db.session.add(owner3)
            
        customer = User.query.filter_by(email='customer@localbiz.com').first()
        if not customer:
            customer = User(
                full_name='Priya Sharma',
                email='customer@localbiz.com',
                phone='9731234567',
                role='customer',
                password_hash=generate_password_hash('Customer@123')
            )
            db.session.add(customer)
            
        customer2 = User.query.filter_by(email='anand@localbiz.com').first()
        if not customer2:
            customer2 = User(
                full_name='Anand Patel',
                email='anand@localbiz.com',
                phone='9611223344',
                role='customer',
                password_hash=generate_password_hash('Customer@123')
            )
            db.session.add(customer2)
            
        db.session.commit()
        
        # 3. Seed Businesses if empty
        if Business.query.count() == 0:
            cat_food = Category.query.filter_by(name='Restaurants & Cafes').first()
            cat_mobile = Category.query.filter_by(name='Mobile & Electronics').first()
            cat_cloth = Category.query.filter_by(name='Clothing & Fashion').first()
            cat_grocery = Category.query.filter_by(name='Grocery & Supermarket').first()
            cat_salon = Category.query.filter_by(name='Salons & Personal Care').first()
            cat_health = Category.query.filter_by(name='Health & Pharmacy').first()
            cat_books = Category.query.filter_by(name='Books & Education').first()
            cat_auto = Category.query.filter_by(name='Auto & Transport').first()
            cat_electric = Category.query.filter_by(name='Electricals & Hardware').first()
            cat_jewelry = Category.query.filter_by(name='Jewelry & Watches').first()
            
            # Shop 1
            b1 = Business(
                owner_id=owner.id,
                category_id=cat_food.id,
                business_name='Local Food Corner & Tiffins',
                description='Authentic local South Indian delicacies, hot dosas, fresh coffee, and family dining in the heart of town.',
                address='Near Gandhi Circle, Main Road',
                city='Hiriyur',
                phone='9845012345',
                email='foodcorner@localbiz.com',
                website='https://foodcorner.localbiz.com',
                status='approved',
                rating=4.6,
                total_reviews=18,
                view_count=320,
                latitude=13.9452,
                longitude=76.6215,
                image_url='https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=500&auto=format&fit=crop&q=60'
            )
            
            # Shop 2
            b2 = Business(
                owner_id=owner.id,
                category_id=cat_mobile.id,
                business_name='Smart Mobile Store & Service',
                description='Latest smartphones, mobile tempered glass, accessories, instant screen replacement, and genuine gadget repairs.',
                address='Opposite Bus Stand, Vani Vilas Road',
                city='Hiriyur',
                phone='9845012346',
                email='smartmobile@localbiz.com',
                status='approved',
                rating=4.4,
                total_reviews=14,
                view_count=275,
                latitude=13.9470,
                longitude=76.6190,
                image_url='https://images.unsplash.com/photo-1511707171634-5f897ff02560?w=500&auto=format&fit=crop&q=60'
            )
            
            # Shop 3
            b3 = Business(
                owner_id=owner2.id,
                category_id=cat_cloth.id,
                business_name='Fashion World & Silk Saree Centre',
                description='Exclusive collection of designer sarees, wedding dresses, casual shirts, jeans, and kids wear at wholesale prices.',
                address='Cloth Market Street, Nehru Bazaar',
                city='Hiriyur',
                phone='9900112233',
                email='fashionworld@localbiz.com',
                status='approved',
                rating=4.7,
                total_reviews=22,
                view_count=410,
                latitude=13.9430,
                longitude=76.6230,
                image_url='https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=500&auto=format&fit=crop&q=60'
            )
            
            # Shop 4
            b4 = Business(
                owner_id=owner2.id,
                category_id=cat_grocery.id,
                business_name='Sri Manjunatha Provision & Supermarket',
                description='Fresh farm vegetables, organic rice, cooking oils, daily spices, and wholesale household groceries with quick doorstep delivery.',
                address='Market Road, Fort Area',
                city='Hiriyur',
                phone='9900112234',
                email='manjunathagrocery@localbiz.com',
                status='approved',
                rating=4.8,
                total_reviews=35,
                view_count=520,
                latitude=13.9460,
                longitude=76.6220,
                image_url='https://images.unsplash.com/photo-1578916171728-46686eac8d58?w=500&auto=format&fit=crop&q=60'
            )
            
            # Shop 5
            b5 = Business(
                owner_id=owner.id,
                category_id=cat_salon.id,
                business_name='Glamour Family Salon & Spa',
                description='Professional hair cutting, herbal facial, bridal makeover, and relaxing grooming packages for men and women.',
                address='1st Floor, City Complex, PB Road',
                city='Hiriyur',
                phone='9845012347',
                email='glamour@localbiz.com',
                status='approved',
                rating=4.5,
                total_reviews=12,
                view_count=190,
                latitude=13.9485,
                longitude=76.6180,
                image_url='https://images.unsplash.com/photo-1560066984-138dadb4c035?w=500&auto=format&fit=crop&q=60'
            )
            
            # Shop 6
            b6 = Business(
                owner_id=owner2.id,
                category_id=cat_food.id,
                business_name='New Town Sweets & Bakery',
                description='Fresh hot puffs, birthday cakes, Mysore Pak, and traditional sweet delicacies baked fresh every morning.',
                address='Near KSRTC Depot Road',
                city='Chitradurga',
                phone='9900112235',
                email='newtownbakery@localbiz.com',
                status='approved',
                rating=4.3,
                total_reviews=10,
                view_count=165,
                latitude=14.2250,
                longitude=76.3980,
                image_url='https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60'
            )

            # Shop 7: Books & Stationery
            b7 = Business(
                owner_id=owner3.id,
                category_id=cat_books.id if cat_books else cat_mobile.id,
                business_name='Sri Raghavendra Book House & Stationery',
                description='School textbooks, VTU engineering guides, competitive exam study materials, branded notebooks, and fine writing pens.',
                address='Near Girls High School, Main Bazaar',
                city='Hiriyur',
                phone='9880123456',
                email='raghavendrabooks@localbiz.com',
                status='approved',
                rating=4.7,
                total_reviews=16,
                view_count=230,
                latitude=13.9442,
                longitude=76.6205,
                image_url='https://images.unsplash.com/photo-1507842229451-7f01be7fe8e7?w=500&auto=format&fit=crop&q=60'
            )

            # Shop 8: Auto & Transport
            b8 = Business(
                owner_id=owner3.id,
                category_id=cat_auto.id if cat_auto else cat_mobile.id,
                business_name='Maruthi Two-Wheeler Care & Auto Spares',
                description='Expert motorbike and scooter mechanics, genuine company oil, battery health checkup, tubeless puncture, and foam wash.',
                address='Bangalore-Bellary Bypass Road',
                city='Hiriyur',
                phone='9880123457',
                email='maruthiauto@localbiz.com',
                status='approved',
                rating=4.6,
                total_reviews=19,
                view_count=285,
                latitude=13.9510,
                longitude=76.6150,
                image_url='https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=500&auto=format&fit=crop&q=60'
            )

            # Shop 9: Electricals & Hardware
            b9 = Business(
                owner_id=owner3.id,
                category_id=cat_electric.id if cat_electric else cat_mobile.id,
                business_name='SLV Electricals & Lighting Showroom',
                description='Energy-saving LED lights, decorative chandeliers, high-speed ceiling fans, modular switches, and house wiring cables.',
                address='Vedavathi Nagar, Near Water Tank',
                city='Hiriyur',
                phone='9880123458',
                email='slvelectricals@localbiz.com',
                status='approved',
                rating=4.5,
                total_reviews=11,
                view_count=175,
                latitude=13.9420,
                longitude=76.6245,
                image_url='https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&auto=format&fit=crop&q=60'
            )

            # Shop 10: Health & Pharmacy
            b10 = Business(
                owner_id=owner.id,
                category_id=cat_health.id,
                business_name='Sanjivini 24x7 Medicals & Clinical Lab',
                description='Prescription allopathic and Ayurvedic medicines, surgical supplies, baby care products, and rapid clinical diagnostic blood tests.',
                address='Government Hospital Circle, PB Road',
                city='Hiriyur',
                phone='9845012348',
                email='sanjivinipharmacy@localbiz.com',
                status='approved',
                rating=4.9,
                total_reviews=28,
                view_count=360,
                latitude=13.9465,
                longitude=76.6200,
                image_url='https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=500&auto=format&fit=crop&q=60'
            )

            # Shop 11: Heritage Khadi & Sarees in Chitradurga
            b11 = Business(
                owner_id=owner2.id,
                category_id=cat_cloth.id,
                business_name='Chitradurga Heritage Khadi & Handlooms',
                description='Handloom cotton shirts, pure khadi kurtas, traditional Ilkal silk sarees with Chikki Paras border, and hand-embroidered shawls.',
                address='Near Historical Fort Entrance, Fort Road',
                city='Chitradurga',
                phone='9900112236',
                email='heritagekhadi@localbiz.com',
                status='approved',
                rating=4.8,
                total_reviews=24,
                view_count=310,
                latitude=14.2230,
                longitude=76.4010,
                image_url='https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=500&auto=format&fit=crop&q=60'
            )

            # Shop 12: Jewelry & Watches
            b12 = Business(
                owner_id=owner3.id,
                category_id=cat_jewelry.id if cat_jewelry else cat_cloth.id,
                business_name='Balaji Gold, Silver & Watch Works',
                description='Certified 92.5 hallmarked sterling silver pooja items, trendy watches, silver anklets, and watch battery/strap servicing.',
                address='Car Street, Near Venkataramana Temple',
                city='Hiriyur',
                phone='9880123459',
                email='balajijewels@localbiz.com',
                status='approved',
                rating=4.7,
                total_reviews=15,
                view_count=210,
                latitude=13.9435,
                longitude=76.6212,
                image_url='https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=500&auto=format&fit=crop&q=60'
            )

            # Shop 13: Highway Family Restaurant
            b13 = Business(
                owner_id=owner.id,
                category_id=cat_food.id,
                business_name='Annapurna Pure Veg Highway Family Restaurant',
                description='Spacious garden dining, South Indian meals, North Indian paneer curries, tandoori rotis, and fresh juices along the national highway.',
                address='NH-48 Highway, Opposite Toll Plaza',
                city='Hiriyur',
                phone='9845012349',
                email='annapurnahighway@localbiz.com',
                status='approved',
                rating=4.6,
                total_reviews=31,
                view_count=450,
                latitude=13.9530,
                longitude=76.6120,
                image_url='https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=500&auto=format&fit=crop&q=60'
            )

            # Shop 14: Computer & Laptop Clinic
            b14 = Business(
                owner_id=owner2.id,
                category_id=cat_mobile.id,
                business_name='QuickFix Laptop & Computer Repair Clinic',
                description='Computer upgrades, SSD installation, broken laptop screen replacement, antivirus, OS reinstallation, and printer cartridge refills.',
                address='BD Road, Opposite Govt Polytechnic',
                city='Chitradurga',
                phone='9900112237',
                email='quickfixpc@localbiz.com',
                status='approved',
                rating=4.5,
                total_reviews=17,
                view_count=240,
                latitude=14.2210,
                longitude=76.3960,
                image_url='https://images.unsplash.com/photo-1588702547919-26089e690ecc?w=500&auto=format&fit=crop&q=60'
            )
            
            db.session.add_all([b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14])
            db.session.commit()
            
            # 4. Seed Products (Expanded for rich Price Comparisons across shops!)
            products = [
                # Food Corner
                Product(business_id=b1.id, product_name='Special Masala Dosa', description='Crispy golden dosa roasted in pure desi ghee with spicy red chutney.', price=65.00, unit='plate'),
                Product(business_id=b1.id, product_name='South Indian Filter Coffee', description='Traditional aromatic frothy brew served in brass dabarah.', price=25.00, unit='cup'),
                Product(business_id=b1.id, product_name='North Indian Thali Combo', description='Complete thali with rotis, paneer curry, dal, rice, curd, and sweet.', price=140.00, unit='thali'),
                
                # Smart Mobile
                Product(business_id=b2.id, product_name='25W Fast Type-C Charger', description='Original fast charger adapter with surge protection and cable.', price=699.00, unit='piece'),
                Product(business_id=b2.id, product_name='Tempered Glass Screen Guard', description='9H edge-to-edge scratch proof tempered protector.', price=150.00, unit='piece'),
                Product(business_id=b2.id, product_name='Wireless Bluetooth Earbuds', description='True wireless earbuds with deep bass and 24hr battery.', price=1299.00, unit='piece'),
                
                # Fashion World
                Product(business_id=b3.id, product_name='Pure Cotton Formal Shirt', description='Breathable pure cotton slim fit shirt for office and occasions.', price=750.00, unit='piece'),
                Product(business_id=b3.id, product_name='Traditional Kanjeevaram Saree', description='Grand silk saree with rich zari border for festivals and weddings.', price=2450.00, unit='piece'),
                Product(business_id=b3.id, product_name='Men Regular Fit Denim Jeans', description='Durable stretchable blue denim jeans.', price=999.00, unit='piece'),
                
                # Sri Manjunatha Provision
                Product(business_id=b4.id, product_name='Sona Masoori Rice (25kg Bag)', description='Aged premium polished Sona Masoori rice bag.', price=1450.00, unit='bag'),
                Product(business_id=b4.id, product_name='Toor Dal (1kg Pack)', description='Unpolished organic toor dal rich in protein.', price=155.00, unit='kg'),
                Product(business_id=b4.id, product_name='Pure Cow Ghee (500ml)', description='Traditional clarified cow milk ghee with aromatic granulations.', price=340.00, unit='jar'),
                
                # Salon
                Product(business_id=b5.id, product_name='Men Deluxe Haircut & Styling', description='Trendy haircut, neck shave, head wash, and blow dry styling.', price=150.00, unit='service'),
                Product(business_id=b5.id, product_name='Herbal Glow Facial Treatment', description='Deep pore cleansing and Ayurvedic glow face massage.', price=650.00, unit='session'),

                # New Town Sweets
                Product(business_id=b6.id, product_name='Pure Desi Ghee Mysore Pak (500g)', description='Traditional melt-in-mouth soft Mysore Pak.', price=280.00, unit='box'),
                Product(business_id=b6.id, product_name='Crispy Vegetable Puff', description='Flaky puff pastry stuffed with spicy potato masala.', price=20.00, unit='piece'),

                # Book House
                Product(business_id=b7.id, product_name='Classmate Long Notebooks (Pack of 6)', description='200 pages ruled long notebook bundle for students.', price=240.00, unit='pack'),
                Product(business_id=b7.id, product_name='Parker Vector Stainless Steel Roller Pen', description='Refillable smooth writing luxury executive pen.', price=350.00, unit='piece'),
                Product(business_id=b7.id, product_name='Casio Scientific Calculator FX-991EX', description='552 functions advanced scientific calculator for engineering students.', price=1295.00, unit='piece'),

                # Auto Spares
                Product(business_id=b8.id, product_name='Castrol Activ 4T 20W-40 Engine Oil (1L)', description='Continuous protection synthetic technology oil for motorbikes.', price=420.00, unit='bottle'),
                Product(business_id=b8.id, product_name='Full Two-Wheeler General Service', description='Engine check, carburetor tuning, oil filter change, and full wash.', price=399.00, unit='service'),

                # Electricals
                Product(business_id=b9.id, product_name='Havells 9W Cool Day LED Bulb (Pack of 4)', description='High lumen energy-efficient LED bulbs with 2 years warranty.', price=299.00, unit='pack'),
                Product(business_id=b9.id, product_name='Crompton High Speed 1200mm Ceiling Fan', description='Aerodynamic blades for superior air delivery and silent motor.', price=1499.00, unit='piece'),
                Product(business_id=b9.id, product_name='25W Fast Type-C Charger', description='Universal heavy-duty 25W wall adapter.', price=649.00, unit='piece'), # Compares with Smart Mobile!

                # Sanjivini Medicals
                Product(business_id=b10.id, product_name='Omron Digital Blood Pressure Monitor', description='Accurate one-touch automatic BP checker with cuff.', price=1850.00, unit='piece'),
                Product(business_id=b10.id, product_name='Complete Blood Count (CBC) Lab Test', description='Full pathology blood profile check with doctor certified report.', price=250.00, unit='test'),

                # Chitradurga Khadi
                Product(business_id=b11.id, product_name='Traditional Pure Khadi Cotton Kurta', description='Handspun eco-friendly breathable summer kurta.', price=650.00, unit='piece'),
                Product(business_id=b11.id, product_name='Pure Cotton Formal Shirt', description='Handloom woven organic cotton shirt.', price=720.00, unit='piece'), # Compares with Fashion World!

                # Balaji Jewels
                Product(business_id=b12.id, product_name='92.5 Pure Sterling Silver Pooja Diya', description='Carved traditional silver oil lamp for home shrine.', price=850.00, unit='piece'),
                Product(business_id=b12.id, product_name='Titan Neo Analog Men Quartz Watch', description='Water resistant stylish stainless steel watch.', price=2195.00, unit='piece'),

                # Annapurna Highway
                Product(business_id=b13.id, product_name='Special Masala Dosa', description='Crispy butter roasted masala dosa with three chutneys and sambar.', price=70.00, unit='plate'), # Compares with Food Corner!
                Product(business_id=b13.id, product_name='North Indian Thali Combo', description='Deluxe thali with paneer sabzi, dal tadka, jeera rice, and gulab jamun.', price=160.00, unit='thali'),

                # QuickFix PC Clinic
                Product(business_id=b14.id, product_name='512GB NVMe High Speed SSD Upgrade', description='Ultra fast SSD drive with free Windows installation.', price=2850.00, unit='piece'),
                Product(business_id=b14.id, product_name='25W Fast Type-C Charger', description='High wattage fast charging brick for mobiles and laptops.', price=680.00, unit='piece') # Compares with Smart Mobile & SLV!
            ]
            db.session.add_all(products)
            
            # 5. Seed Special Offers
            offers = [
                Offer(business_id=b1.id, title='Weekend Family Dining 15% OFF', description='Enjoy flat 15% discount on all family dinner orders above ₹500.', discount_percent=15.00, coupon_code='WEEKEND15', valid_until=date.today() + timedelta(days=20), clicks_count=84),
                Offer(business_id=b2.id, title='Free Tempered Glass with Screen Repair', description='Get a free 9H tempered glass screen protector with any display replacement.', discount_percent=100.00, coupon_code='SCREENFREE', valid_until=date.today() + timedelta(days=15), clicks_count=62),
                Offer(business_id=b3.id, title='Festival Bonanza: 20% OFF on Sarees', description='Special festival discount on all designer sarees and bridal wear.', discount_percent=20.00, coupon_code='FESTIVAL20', valid_until=date.today() + timedelta(days=30), clicks_count=115),
                Offer(business_id=b4.id, title='Grocery Saver: Flat ₹50 OFF', description='Save ₹50 instantly on grocery orders over ₹800.', discount_percent=10.00, coupon_code='GROCERY50', valid_until=date.today() + timedelta(days=25), clicks_count=98),
                Offer(business_id=b7.id, title='Student Special: 10% OFF on Books', description='Exclusive educational discount on all textbooks and engineering guides.', discount_percent=10.00, coupon_code='STUDENT10', valid_until=date.today() + timedelta(days=40), clicks_count=45),
                Offer(business_id=b8.id, title='Free Foam Bike Wash with Service', description='Complete high-pressure foam wash included free with bike general servicing.', discount_percent=100.00, coupon_code='FREEWASH', valid_until=date.today() + timedelta(days=30), clicks_count=73),
                Offer(business_id=b10.id, title='Senior Citizen Care: Flat 12% OFF', description='Flat 12% concession on all prescription medicines and home test kits.', discount_percent=12.00, coupon_code='CARE12', valid_until=date.today() + timedelta(days=60), clicks_count=52),
                Offer(business_id=b11.id, title='Handloom Utsav: 15% OFF on Kurtas', description='Special handloom festival rebate on pure khadi shirts and kurtas.', discount_percent=15.00, coupon_code='KHADI15', valid_until=date.today() + timedelta(days=20), clicks_count=39)
            ]
            db.session.add_all(offers)
            
            # 6. Seed Reviews
            reviews = [
                Review(business_id=b1.id, user_id=customer.id, rating=5, comment='Best crispy masala dosa in Hiriyur! Clean seating, friendly staff, and great coffee.'),
                Review(business_id=b1.id, user_id=customer2.id, rating=4, comment='Very tasty meals and quick service. Great place for family lunches.'),
                Review(business_id=b2.id, user_id=customer.id, rating=5, comment='Replaced my broken phone display in 1 hour at a very fair price. Highly recommended!'),
                Review(business_id=b3.id, user_id=customer2.id, rating=5, comment='Excellent saree collection and fair pricing. Bought wedding sarees here for my family.'),
                Review(business_id=b4.id, user_id=customer.id, rating=5, comment='Everything available under one roof at genuine wholesale rates. Free home delivery too!'),
                Review(business_id=b7.id, user_id=customer.id, rating=5, comment='Got all my semester engineering textbooks under one roof. Friendly uncle and fair student discount.'),
                Review(business_id=b8.id, user_id=customer2.id, rating=5, comment='Serviced my Activa scooter here. Engine runs super smooth now and the free wash was very thorough!'),
                Review(business_id=b10.id, user_id=customer.id, rating=5, comment='Emergency medicines available late at night. Extremely helpful pharmacists.')
            ]
            db.session.add_all(reviews)
            
            # 7. Seed Enquiries
            enquiries = [
                Enquiry(business_id=b1.id, user_id=customer.id, customer_name='Priya Sharma', customer_phone='9731234567', customer_email='customer@localbiz.com', message='Do you take outdoor catering orders for a family birthday event of 50 people this Sunday?', status='new'),
                Enquiry(business_id=b2.id, user_id=customer2.id, customer_name='Anand Patel', customer_phone='9611223344', customer_email='anand@localbiz.com', message='Is OnePlus Nord CE 3 screen replacement part available in stock?', status='replied', reply_message='Yes Anand, original display is in stock. Please visit our shop between 10 AM and 8 PM.'),
                Enquiry(business_id=b3.id, user_id=customer.id, customer_name='Priya Sharma', customer_phone='9731234567', customer_email='customer@localbiz.com', message='Can you share pictures of pure Ilkal handloom sarees in red and green?', status='read'),
                Enquiry(business_id=b7.id, user_id=customer2.id, customer_name='Anand Patel', customer_phone='9611223344', customer_email='anand@localbiz.com', message='Is VTU 5th semester Computer Science question bank available?', status='replied', reply_message='Yes, new syllabus question bank with solved papers is available. Please drop by.')
            ]
            db.session.add_all(enquiries)
            
            # 8. Seed Views and Searches for Market Analytics
            for day_offset in range(14, 0, -1):
                view_date = datetime.utcnow() - timedelta(days=day_offset)
                db.session.add(BusinessView(business_id=b1.id, ip_address='192.168.1.10', viewed_at=view_date))
                db.session.add(BusinessView(business_id=b4.id, ip_address='192.168.1.15', viewed_at=view_date))
                db.session.add(BusinessView(business_id=b7.id, ip_address='192.168.1.30', viewed_at=view_date))
                if day_offset % 2 == 0:
                    db.session.add(BusinessView(business_id=b2.id, ip_address='192.168.1.20', viewed_at=view_date))
                    db.session.add(BusinessView(business_id=b3.id, ip_address='192.168.1.25', viewed_at=view_date))
                    db.session.add(BusinessView(business_id=b10.id, ip_address='192.168.1.35', viewed_at=view_date))
                    
            searches = [
                SearchHistory(search_query='dosa', category_filter='Restaurants & Cafes', location_filter='Hiriyur'),
                SearchHistory(search_query='mobile repair', category_filter='Mobile & Electronics', location_filter='Hiriyur'),
                SearchHistory(search_query='saree', category_filter='Clothing & Fashion', location_filter='Hiriyur'),
                SearchHistory(search_query='rice bag', category_filter='Grocery & Supermarket', location_filter='Hiriyur'),
                SearchHistory(search_query='haircut', category_filter='Salons & Personal Care', location_filter='Hiriyur'),
                SearchHistory(search_query='books engineering', category_filter='Books & Education', location_filter='Hiriyur'),
                SearchHistory(search_query='bike service oil', category_filter='Auto & Transport', location_filter='Hiriyur'),
                SearchHistory(search_query='medicine bp', category_filter='Health & Pharmacy', location_filter='Hiriyur')
            ]
            db.session.add_all(searches)
            
            db.session.commit()
            print("Database initialized and fully seeded with 14 diverse shops and realistic data.")
