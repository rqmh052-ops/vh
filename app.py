from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import base64
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# صورة الأسد المستخدمة في الطلب (تم تحويلها إلى base64 كما في الكود الأصلي)
IMAGE_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj2T0W-oALk1u5PRF9YvBClDd7ycxpWc54AeAFlzzGStIvOhSBSouwRa5csreSZeAiDSPlBEmMALyxVYO-aPTReJ3CQeFS3Q2cBDN0mliP15RV9xD8ID2YIuyD7i9rcbVCcb0r1AOn-RCk9/s829/%25D8%25B5%25D9%2588%25D8%25B1-%25D8%25B9%25D9%258A%25D8%25A7%25D9%2584-%25D8%25AE%25D9%2584%25D9%2581%25D9%258A%25D8%25A7%25D8%25AA-%25D8%25B1%25D9%2585%25D8%25B2%25D9%258A%25D8%25A7%25D8%25AA-%25D8%25B9%25D9%258A%25D8%25A7%25D9%2584+%25282%2529.jpg"

def get_image_base64():
    try:
        resp = requests.get(IMAGE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode("utf-8")
    except:
        # إذا فشل تحميل الصورة نستخدم صورة بديلة فارغة
        return ""

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/login', methods=['POST'])
def handle_login():
    data = request.get_json()
    number = data.get('phone')
    password = data.get('password')

    if not number or not password:
        return jsonify({"status": "error", "message": "بيانات ناقصة"}), 400

    # 1. الحصول على access_token
    token_url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    payload = {
        'grant_type': "password",
        'username': number,
        'password': password,
        'client_secret': "dca0pbLUWXVhXR266Gw1iT5rqwvvJQoN",
        'client_id': "AnaVF"
    }
    headers_token = {
        'User-Agent': "okhttp/4.12.0",
        'Accept': "application/json, text/plain, */*",
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
        token_resp = requests.post(token_url, data=payload, headers=headers_token, timeout=15)
        if token_resp.status_code != 200:
            return jsonify({"status": "لم يأخذها بسبب كلمة مرور خاطئة", "title": "خطأ في كلمة المرور", "desc": "بيانات المرور غير صحيحة."})
        token = token_resp.json().get('access_token')
        if not token:
            return jsonify({"status": "لم يأخذها بسبب كلمة مرور خاطئة", "title": "خطأ في كلمة المرور", "desc": "لم نتمكن من المصادقة."})
    except Exception:
        return jsonify({"status": "خطأ في الاتصال بالخادم", "title": "مشكلة في الشبكة", "desc": "تعذر الاتصال بخوادم فودافون."})

    # 2. الحصول على id العرض
    promo_url = "https://web.vodafone.com.eg/services/dxl/promo/promotion"
    params = {'@type': 'Promo', '$.context.type': 'worldCupWow26'}
    headers_promo = {
        'User-Agent': "vodafoneandroid",
        'Accept': "application/json",
        'Authorization': f"Bearer {token}",
        'msisdn': number,
        'clientId': "WebsiteConsumer",
        'channel': "APP_PORTAL",
        'Content-Type': "application/json"
    }
    try:
        promo_resp = requests.get(promo_url, params=params, headers=headers_promo, timeout=15)
        if promo_resp.status_code != 200 or not promo_resp.json():
            return jsonify({"status": "أخذها مسبقاً", "title": "الهدية مستخدمة", "desc": "هذا الرقم حصل على العرض مسبقاً."})
        promo_id = promo_resp.json()[0]["id"]
    except Exception:
        return jsonify({"status": "خطأ في الاتصال بالخادم", "title": "مشكلة في الخادم", "desc": "تعذر الحصول على بيانات العرض."})

    # 3. إرسال الطلب النهائي لتفعيل الهدية
    image_b64 = get_image_base64()
    journey_url = "https://web.vodafone.com.eg/services/dxl/pj/wc/journey/promoJourney"
    journey_payload = {
        "@type": "worldCupWow26",
        "id": promo_id,
        "attachment": [
            {
                "attachmentType": "Image",
                "content": image_b64,
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
    headers_journey = {
        'User-Agent': "vodafoneandroid",
        'Accept': "application/json",
        'Content-Type': "application/json",
        'Authorization': f"Bearer {token}",
        'msisdn': number,
        'clientId': "WebsiteConsumer",
        'Origin': "https://web.vodafone.com.eg"
    }
    try:
        final_resp = requests.post(journey_url, json=journey_payload, headers=headers_journey, timeout=20)
        if final_resp.status_code == 201:
            return jsonify({"status": "تم أخذ الهدية بنجاح", "title": "تم تفعيل الهدية! 🎉", "desc": "تم تفعيل حزمة 500 ميجابايت على خطك."})
        else:
            # محاولة قراءة سبب الفشل
            reason = final_resp.json().get("reason", "عذراً، لم يتم التفعيل.")
            if "already" in reason.lower() or "taken" in reason.lower():
                return jsonify({"status": "أخذها مسبقاً", "title": "أخذتها مسبقاً", "desc": reason})
            else:
                return jsonify({"status": "لم يأخذها بسبب كلمة مرور خاطئة", "title": "فشل التفعيل", "desc": reason})
    except Exception as e:
        return jsonify({"status": "خطأ في الاتصال بالخادم", "title": "مشكلة في الخادم", "desc": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))