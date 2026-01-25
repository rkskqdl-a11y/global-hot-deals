import os
import time
import random
import hmac
import hashlib
import requests
import json
from datetime import datetime

# 1. 환경 변수 설정
ALI_APP_KEY = os.environ.get("ALI_APP_KEY", "").strip()
ALI_SECRET = os.environ.get("ALI_SECRET", "").strip()
ALI_TRACKING_ID = os.environ.get("ALI_TRACKING_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 2. 무한 키워드 생성기 (2,450개 조합)
def get_massive_keyword_list():
    modifiers = [
        "Best Budget", "Top Rated", "High Quality", "Portable", "Wireless", 
        "Bluetooth", "Gaming", "RGB", "Mechanical", "Silent", 
        "Heavy Duty", "Fast Charging", "Ultralight", "Waterproof", "Foldable", 
        "Type-C", "Magnetic", "Smart", "IoT", "Minimalist", 
        "Travel Friendly", "Professional", "Gift for Him", "Gift for Her", "Trending",
        "Xiaomi", "Lenovo", "Baseus", "Anker Style", "Must Have", "Outdoor", "Home Office", "Car Accessory", "Kitchen Gear", "Emergency"
    ]
    products = [
        "Mechanical Keyboard", "Vertical Mouse", "Gaming Mouse", "Power Bank", "USB Hub",
        "GaN Charger", "Monitor Light Bar", "Monitor Arm", "Tablet Stand", "Laptop Stand",
        "Smartphone Gimbal", "Bluetooth Speaker", "TWS Earbuds", "Noise Cancelling Headphones",
        "Smart Watch", "Apple Watch Strap", "iPad Case", "NVMe SSD Enclosure", "USB Flash Drive",
        "Mini PC", "Portable Projector", "TV Stick", "Air Purifier", "Humidifier",
        "Robot Vacuum", "Cordless Vacuum", "Hair Dryer", "Electric Toothbrush", "Water Flosser",
        "Smart Scale", "Desk Fan", "Portable Monitor", "Nintendo Switch Accessories", "PS5 Stand",
        "Drone 4K", "Action Camera", "Dash Cam", "Security Camera", "Smart Doorbell", "Car Vacuum Cleaner", "Tire Inflator", "Jump Starter", "OBD2 Scanner", "Car Wash Towel",
        "Car Organizer", "Car Phone Holder", "Wireless Car Charger", "Head Up Display", "Car Trash Bin", "Camping Chair", "Camping Table", "Camping Lantern", "LED Flashlight", "Camping Stove",
        "Titanium Cup", "Sleeping Bag", "Inflatable Mat", "Camping Tent", "Fishing Reel",
        "Fishing Rod", "Lure Set", "Trekking Poles", "Bicycle Light", "Bike Computer",
        "Tactical Backpack", "Survival Kit", "Multitool", "Pocket Knife", "Heated Vest"
    ]
    
    all_keywords = [f"{m} {p}" for m in modifiers for p in products]
    return all_keywords

def get_ali_products(keyword):
    url = "https://api-sg.aliexpress.com/sync"
    params = {
        "app_key": ALI_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "method": "aliexpress.affiliate.product.query",
        "partner_id": "apidoc",
        "keywords": keyword,
        "target_currency": "USD",
        "target_language": "EN",
        "sort": "LAST_VOLUME_DESC",
        "tracking_id": ALI_TRACKING_ID,
        "page_size": "10"
    }
    
    sorted_params = sorted(params.items())
    base_string = "".join([f"{k}{v}" for k, v in sorted_params])
    sign = hmac.new(ALI_SECRET.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    params["sign"] = sign
    
    try:
        response = requests.post(url, data=params)
        data = response.json()
        
        # 🔍 안전한 데이터 파싱 (에러 방지)
        query_resp = data.get("aliexpress_affiliate_product_query_response", {})
        resp_result = query_resp.get("resp_result", {})
        result_data = resp_result.get("result", {})
        
        if result_data and "products" in result_data:
            return result_data["products"]["product"]
            
        print(f"DEBUG: Ali API No Data Found. Response: {json.dumps(data)}")
        return []
    except Exception as e:
        print(f"DEBUG: Ali API Exception: {e}")
        return []

def generate_blog_content(product):
    # 🚀 제미나이 3.0 프로 엔진 호출 (2026년 기준 최신 엔진)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.0-pro:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    prompt_text = f"As a tech expert using Gemini 3.0, write a professional English review for: {product.get('product_title')}. Price: ${product.get('target_sale_price')}. Focus on value and features. Use Markdown."
    
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        # 3.0 모델명 오류 시 1.5로 자동 전환 (안전장치)
        if "error" in result:
            url = url.replace("gemini-3.0-pro", "gemini-1.5-flash")
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()

        return result["candidates"][0]["content"]["parts"][0]["text"]
    except: return None

def main():
    # 1. 초기 설정
    os.makedirs("posts", exist_ok=True)
    
    # 2. 키워드 생성 및 출력 (가시성 확보)
    all_keywords = get_massive_keyword_list()
    print(f"📚 Total Keywords Loaded: {len(all_keywords)}") # 키워드 개수 확인 가능
    
    target_keyword = random.choice(all_keywords)
    print(f"🎯 Selected Target Keyword: {target_keyword}")

    # 3. 상품 검색
    products = get_ali_products(target_keyword)
    if not products:
        print("❌ No products found. Checking if API keys are valid.")
        return

    # 4. 글 생성 및 저장
    selected_product = products[0]
    print(f"📝 Writing Gemini 3.0 Review: {selected_product['product_title'][:40]}...")
    
    content = generate_blog_content(selected_product)
    if content:
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = f"posts/{today}-post.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"🎉 SUCCESS: {file_path} created!")
    else:
        print("❌ Content generation failed.")

if __name__ == "__main__":
    main()
