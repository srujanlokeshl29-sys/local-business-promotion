import re
from datetime import date
from flask import url_for
from models import db, Business, Product, Offer, Category

def generate_ai_response(user_query, lang='en', user_lat=None, user_lng=None):
    """
    LocalBiz AI Assistant: Generates intelligent, context-aware answers in English or Kannada
    using actual database records (businesses, products, prices, offers, and locations).
    """
    query = (user_query or '').strip().lower()
    
    # Auto-detect Kannada language if user types Kannada Unicode characters
    has_kannada_chars = bool(re.search(r'[\u0C80-\u0CFF]', user_query))
    if has_kannada_chars:
        lang = 'kn'
        
    response_text = ""
    suggested_actions = []
    
    # 1. GREETINGS
    greetings = ['hi', 'hello', 'hey', 'namaskara', 'namaste', 'good morning', 'good evening', 'who are you', 'ನಮಸ್ಕಾರ', 'ಹಲೋ', 'ಹಾಯ್']
    if any(g in query for g in greetings) and len(query.split()) <= 4:
        if lang == 'kn':
            response_text = (
                "ನಮಸ್ಕಾರ! 🙏 ನಾನು ನಿಮ್ಮ **ಲೋಕಲ್ ಬಿಜ್ AI ಸಹಾಯಕ** (LocalBiz Smart Assistant).\n\n"
                "ಹಿರಿಯೂರು, ಚಿತ್ರದುರ್ಗ ಹಾಗೂ ಸುತ್ತಮುತ್ತಲಿನ ಸ್ಥಳೀಯ ಅಂಗಡಿಗಳು, ಉತ್ಪನ್ನಗಳ ಬೆಲೆ ಹೋಲಿಕೆ, "
                "ವಿಶೇಷ ರಿಯಾಯಿತಿ ಕೂಪನ್‌ಗಳು ಮತ್ತು ಸ್ಥಳದ ಮಾಹಿತಿ ಪಡೆಯಲು ನಾನು ನಿಮಗೆ ನೆರವಾಗಬಲ್ಲೆ.\n\n"
                "ನೀವು ಏನು ಹುಡುಕುತ್ತಿದ್ದೀರಿ?"
            )
        else:
            response_text = (
                "Hello and welcome! 👋 I am your **LocalBiz AI Assistant**.\n\n"
                "I can help you discover verified local shops in **Hiriyur, Chitradurga**, "
                "compare product prices across neighborhood stores, find active discount coupons, and track store locations.\n\n"
                "How can I assist you today?"
            )
        return {
            'reply': response_text,
            'suggestions': [
                'Top rated restaurants in Hiriyur' if lang == 'en' else 'ಹಿರಿಯೂರಿನ ಉತ್ತಮ ಉಪಹಾರ ಗೃಹಗಳು',
                'Compare price of 25W fast charger' if lang == 'en' else 'ಫಾಸ್ಟ್ ಚಾರ್ಜರ್ ಬೆಲೆ ಹೋಲಿಕೆ',
                'Show active discount coupons' if lang == 'en' else 'ವಿಶೇಷ ರಿಯಾಯಿತಿ ಕೂಪನ್‌ಗಳು',
                'Where to service my two-wheeler?' if lang == 'en' else 'ಟೂ-ವೀಲರ್ ಸರ್ವೀಸ್ ಅಂಗಡಿಗಳು'
            ],
            'actions': []
        }

    # 2. SPECIAL OFFERS & COUPONS INTENT
    if any(k in query for k in ['offer', 'discount', 'coupon', 'deal', 'save', 'cheap', 'ಕೂಪನ್', 'ರಿಯಾಯಿತಿ', 'ಆಫರ್', 'ಕೊಡುಗೆ']):
        active_offers = Offer.query.join(Business).filter(Business.status == 'approved', Offer.is_active == True, Offer.valid_until >= date.today())\
                                   .order_by(Offer.discount_percent.desc()).limit(4).all()
        if active_offers:
            if lang == 'kn':
                response_text = "🎉 **ಪ್ರಸ್ತುತ ಸಕ್ರಿಯವಾಗಿರುವ ಸ್ಥಳೀಯ ವಿಶೇಷ ಕೊಡುಗೆಗಳು ಮತ್ತು ಕೂಪನ್‌ಗಳು:**\n\n"
                for o in active_offers:
                    response_text += f"• **{o.title}** ({o.business.business_name}, {o.business.city})\n"
                    response_text += f"  🏷️ **{o.discount_percent}% ರಿಯಾಯಿತಿ** | ಕೂಪನ್ ಕೋಡ್: `{o.coupon_code or 'Walk-in'}` (ಮಾನ್ಯತೆ: {o.valid_until.strftime('%d %b')})\n\n"
            else:
                response_text = "🎉 **Here are the best active local discount offers & coupons:**\n\n"
                for o in active_offers:
                    response_text += f"• **{o.title}** at *{o.business.business_name}* ({o.business.city})\n"
                    response_text += f"  🏷️ **{o.discount_percent}% OFF** | Code: `{o.coupon_code or 'Walk-in'}` | Valid until: {o.valid_until.strftime('%d %b, %Y')}\n\n"
            suggested_actions.append({'label': 'View All Offers', 'url': url_for('offers_page')})
        else:
            response_text = "Currently, no new offers are posted. Check back soon!" if lang == 'en' else "ಸದ್ಯಕ್ಕೆ ಯಾವುದೇ ಹೊಸ ಆಫರ್‌ಗಳಿಲ್ಲ. ಶೀಘ್ರದಲ್ಲೇ ಪರಿಶೀಲಿಸಿ!"
            
        return {
            'reply': response_text,
            'suggestions': ['Compare product prices', 'Top rated shops near me', 'Find grocery stores'],
            'actions': suggested_actions
        }

    # 3. PRICE COMPARISON INTENT
    price_keywords = ['price', 'cost', 'rate', 'compare', 'how much', 'ಬೆಲೆ', 'ದರ', 'ಎಷ್ಟು', 'ಹೋಲಿಕೆ']
    if any(k in query for k in price_keywords) or any(p in query for p in ['charger', 'rice', 'shirt', 'saree', 'oil', 'dosa', 'notebook', 'fan', 'ssd']):
        # Find matching products
        search_terms = [w for w in query.split() if len(w) > 3 and w not in price_keywords]
        prod_matches = []
        if search_terms:
            for term in search_terms:
                matches = Product.query.join(Business).filter(Business.status == 'approved', Product.product_name.ilike(f"%{term}%")).all()
                if matches:
                    prod_matches.extend(matches)
        else:
            prod_matches = Product.query.join(Business).filter(Business.status == 'approved').limit(6).all()

        if prod_matches:
            # Group by product name
            grouped = {}
            for p in prod_matches:
                pname = p.product_name.strip()
                if pname not in grouped:
                    grouped[pname] = []
                grouped[pname].append(p)

            if lang == 'kn':
                response_text = "⚖️ **ಸ್ಥಳೀಯ ಅಂಗಡಿಗಳ ಉತ್ಪನ್ನಗಳ ನೈಜ ಬೆಲೆ ಹೋಲಿಕೆ:**\n\n"
                for name, items in list(grouped.items())[:3]:
                    response_text += f"📦 **{name}**:\n"
                    for item in sorted(items, key=lambda x: x.price):
                        response_text += f"  • ₹{item.price:.2f} ({item.unit}) - *{item.business.business_name}* ({item.business.city})\n"
                    response_text += "\n"
            else:
                response_text = "⚖️ **Live Price Comparison across local neighborhood stores:**\n\n"
                for name, items in list(grouped.items())[:3]:
                    response_text += f"📦 **{name}**:\n"
                    for item in sorted(items, key=lambda x: x.price):
                        response_text += f"  • **₹{item.price:.2f}** per {item.unit} at *{item.business.business_name}* ({item.business.city})\n"
                    response_text += "\n"
            suggested_actions.append({'label': 'Open Price Comparison Tool', 'url': url_for('compare_prices')})
            return {
                'reply': response_text,
                'suggestions': ['Check active discounts', 'Find electronics shops', 'Restaurants near me'],
                'actions': suggested_actions
            }

    # 4. LOCATION & DISTANCE TRACKING INTENT
    if any(k in query for k in ['near me', 'location', 'distance', 'track', 'where is', 'direction', 'ಹತ್ತಿರ', 'ಎಲ್ಲಿದೆ', 'ದೂರ']):
        biz_list = Business.query.filter_by(status='approved').all()
        if user_lat and user_lng:
            # Sort by distance
            with_dist = []
            for b in biz_list:
                d = b.distance_from(user_lat, user_lng)
                if d is not None:
                    with_dist.append((b, d))
            with_dist.sort(key=lambda x: x[1])
            top_nearby = with_dist[:4]

            if lang == 'kn':
                response_text = f"📍 **ನಿಮ್ಮ ಸ್ಥಳದಿಂದ ಹತ್ತಿರವಿರುವ ಅಂಗಡಿಗಳು (ಜಿಪಿಎಸ್ ಆಧಾರಿತ):**\n\n"
                for b, dist in top_nearby:
                    response_text += f"• **{b.business_name}** ({b.category.name})\n"
                    response_text += f"  📏 ದೂರ: **~{dist} ಕಿ.ಮೀ** | ⭐ {b.rating} | 📍 {b.address}, {b.city}\n\n"
            else:
                response_text = f"📍 **Top Verified Shops closest to your current location:**\n\n"
                for b, dist in top_nearby:
                    response_text += f"• **{b.business_name}** ({b.category.name})\n"
                    response_text += f"  📏 Distance: **~{dist} km** | ⭐ {b.rating}/5 | 📍 {b.address}, {b.city}\n\n"
            suggested_actions.append({'label': 'Explore Near Me on Map', 'url': url_for('explore') + '?sort=nearest'})
            return {
                'reply': response_text,
                'suggestions': ['Show restaurant near me', 'Show medicals near me', 'Compare prices'],
                'actions': suggested_actions
            }
        else:
            if lang == 'kn':
                response_text = "📍 ನಿಮ್ಮ ಹತ್ತಿರವಿರುವ ಅಂಗಡಿಗಳನ್ನು ನಿಖರವಾಗಿ ತಿಳಿಯಲು ಕೆಳಗಿನ **'ಸ್ಥಳ ಟ್ರ್ಯಾಕ್ ಮಾಡಿ'** ಬಟನ್ ಕ್ಲಿಕ್ ಮಾಡಿ ಅಥವಾ ಜಿಪಿಎಸ್ ಆನ್ ಮಾಡಿ. ಹಿರಿಯೂರು ಮತ್ತು ಚಿತ್ರದುರ್ಗದಲ್ಲಿ ನಮ್ಮಲ್ಲಿ ನೋಂದಾಯಿತ ಅಂಗಡಿಗಳಿವೆ!"
            else:
                response_text = "📍 To get exact distances from your location, click the **'Detect My Location'** button on the Explore page! Currently we have verified shops across **Hiriyur** and **Chitradurga**."
            suggested_actions.append({'label': 'Detect My Location', 'url': url_for('explore')})
            return {
                'reply': response_text,
                'suggestions': ['Shops in Hiriyur', 'Shops in Chitradurga', 'Show best offers'],
                'actions': suggested_actions
            }

    # 5. CATEGORY OR SPECIFIC SEARCH LOOKUP
    category_match = None
    all_cats = Category.query.all()
    for cat in all_cats:
        cname = cat.name.lower()
        kname = cat.kannada_name.lower()
        if any(w in query for w in cname.split()) or any(w in query for w in kname.split()):
            category_match = cat
            break

    # Look up businesses matching query or category
    matched_biz = []
    if category_match:
        matched_biz = Business.query.filter_by(category_id=category_match.id, status='approved').order_by(Business.rating.desc()).limit(4).all()
    else:
        # Match by words in query
        words = [w for w in query.split() if len(w) > 2]
        if words:
            term = words[0]
            matched_biz = Business.query.filter_by(status='approved').filter(
                (Business.business_name.ilike(f"%{term}%")) |
                (Business.description.ilike(f"%{term}%")) |
                (Business.city.ilike(f"%{term}%"))
            ).order_by(Business.rating.desc()).limit(4).all()

    if matched_biz:
        if lang == 'kn':
            response_text = f"🏪 **ನೀವು ಕೇಳಿದ ಪ್ರಶ್ನೆಗೆ ಹೊಂದಿಕೆಯಾಗುವ ಪ್ರಮುಖ ಸ್ಥಳೀಯ ಅಂಗಡಿಗಳು:**\n\n"
            for b in matched_biz:
                dist_str = f" (~{b.distance_from(user_lat, user_lng)} ಕಿ.ಮೀ)" if (user_lat and user_lng and b.distance_from(user_lat, user_lng)) else ""
                response_text += f"• **{b.business_name}** {b.category.icon}\n"
                response_text += f"  ⭐ {b.rating}/5 ({b.total_reviews} ವಿಮರ್ಶೆಗಳು) | 📍 {b.address}, {b.city}{dist_str}\n"
                response_text += f"  📞 {b.phone}\n\n"
        else:
            response_text = f"🏪 **Here are the top local businesses matching your query:**\n\n"
            for b in matched_biz:
                dist_str = f" (~{b.distance_from(user_lat, user_lng)} km away)" if (user_lat and user_lng and b.distance_from(user_lat, user_lng)) else ""
                response_text += f"• **{b.business_name}** {b.category.icon}\n"
                response_text += f"  ⭐ {b.rating}/5 ({b.total_reviews} reviews) | 📍 {b.address}, {b.city}{dist_str}\n"
                response_text += f"  📞 Call: {b.phone}\n\n"
        suggested_actions.append({'label': 'View in Explore Directory', 'url': url_for('explore')})
        return {
            'reply': response_text,
            'suggestions': ['Check their discounts & offers', 'Compare product prices', 'Get directions'],
            'actions': suggested_actions
        }

    # 6. PLATFORM FAQ (Registration, writing reviews, admin, etc.)
    if any(k in query for k in ['register', 'join', 'add my shop', 'owner', 'ನೋಂದಣಿ']):
        if lang == 'kn':
            response_text = (
                "🏪 **ವ್ಯಾಪಾರಿಗಳಿಗಾಗಿ ಸುಲಭ ನೋಂದಣಿ ಪ್ರಕ್ರಿಯೆ:**\n\n"
                "1. ಮೇಲಿನ ಮೆನುವಿನಲ್ಲಿ **'ನೋಂದಣಿ' (Register)** ಕ್ಲಿಕ್ ಮಾಡಿ.\n"
                "2. ಖಾತೆಯ ಪ್ರಕಾರದಲ್ಲಿ **'Business Owner'** ಆಯ್ಕೆಮಾಡಿ.\n"
                "3. ಲಾಗಿನ್ ಆದ ನಂತರ ನಿಮ್ಮ ಅಂಗಡಿಯ ಹೆಸರು, ವಿಳಾಸ ಮತ್ತು ಉತ್ಪನ್ನಗಳನ್ನು ಸೇರಿಸಿ.\n"
                "4. ಅಡ್ಮಿನ್ ಪರಿಶೀಲಿಸಿದ ನಂತರ ನಿಮ್ಮ ಅಂಗಡಿ ನೇರವಾಗಿ ಹುಡುಕಾಟದಲ್ಲಿ ಕಾಣಿಸುತ್ತದೆ!"
            )
        else:
            response_text = (
                "🏪 **How to Register Your Business on LocalBiz:**\n\n"
                "1. Click **Register** on the top navigation bar.\n"
                "2. Choose **Business Owner** under account type.\n"
                "3. Fill in your shop details (Name, Category, Location, Phone, Photo).\n"
                "4. Add your products/services and publish discount coupons.\n"
                "5. Once verified by Admin, customers can discover your shop and send enquiries directly!"
            )
        suggested_actions.append({'label': 'Register as Business Owner', 'url': url_for('register') + '?type=owner'})
        return {
            'reply': response_text,
            'suggestions': ['Explore local shops', 'Special discounts', 'Price comparison'],
            'actions': suggested_actions
        }

    # 7. DEFAULT / FALLBACK HELPFUL GUIDANCE
    if lang == 'kn':
        response_text = (
            f"ನಾನು ಹಿರಿಯೂರು ಮತ್ತು ಚಿತ್ರದುರ್ಗದ ಸ್ಥಳೀಯ ಅಂಗಡಿಗಳು, ಉತ್ಪನ್ನಗಳ ಬೆಲೆ, ಕೊಡುಗೆಗಳು ಮತ್ತು ವಿಳಾಸದ ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡಬಲ್ಲೆ.\n\n"
            f"ಉದಾಹರಣೆಗೆ ಹೀಗೆ ಕೇಳಿ:\n"
            f"• *'ಹಿರಿಯೂರಿನಲ್ಲಿ ಉತ್ತಮ ಊಟದ ಹೋಟೆಲ್ ಯಾವುದು?'*\n"
            f"• *'25W ಮೊಬೈಲ್ ಚಾರ್ಜರ್ ಬೆಲೆ ಎಷ್ಟು?'*\n"
            f"• *'ವಿಶೇಷ ರಿಯಾಯಿತಿ ಕೂಪನ್‌ಗಳನ್ನು ತೋರಿಸು'*\n"
            f"• *'ನನ್ನ ಹತ್ತಿರವಿರುವ ಮೆಡಿಕಲ್ ಶಾಪ್ ಯಾವುದು?'*"
        )
    else:
        response_text = (
            f"I couldn't find exact matches for *'{user_query}'*, but I can help you with:\n\n"
            f"• **Finding Local Shops:** Ask *'Best restaurants in Hiriyur'* or *'Where to buy books?'*\n"
            f"• **Price Comparisons:** Ask *'Price of rice'* or *'How much is 25W charger?'*\n"
            f"• **Discounts & Deals:** Ask *'Show discount coupons'*\n"
            f"• **Near Me Tracking:** Click *'Detect My Location'* to see nearest shops."
        )
    return {
        'reply': response_text,
        'suggestions': [
            'Best restaurants in Hiriyur' if lang == 'en' else 'ಹಿರಿಯೂರಿನ ಉತ್ತಮ ರೆಸ್ಟೋರೆಂಟ್‌ಗಳು',
            'Compare mobile charger prices' if lang == 'en' else 'ಮೊಬೈಲ್ ಚಾರ್ಜರ್ ಬೆಲೆ ಹೋಲಿಕೆ',
            'Show active discount coupons' if lang == 'en' else 'ವಿಶೇಷ ರಿಯಾಯಿತಿ ಕೂಪನ್‌ಗಳು',
            'Nearest shops to me' if lang == 'en' else 'ನನ್ನ ಹತ್ತಿರವಿರುವ ಅಂಗಡಿಗಳು'
        ],
        'actions': [{'label': 'Browse All Businesses', 'url': url_for('explore')}]
    }
