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

def get_random_keyword():
    # 🎯 상품 고갈을 막기 위해 검색어를 아주 구체적이고 랜덤하게 조합합니다.
    prefixes = ["Mini", "Portable", "Wireless", "Smart", "Professional", "Luxury", "Budget", "DIY", "Outdoor", "Home"]
    items = ["Gadget", "Tool", "Electronics", "Adapter", "Sensor", "Controller", "Light", "Charger", "Fan", "Hub"]
    suffixes = ["2026", "New", "Top", "Best", "Trending", "Unique", "Essential"]
    return f"{random.choice(prefixes)} {random.choice(items)} {random.choice(suffixes)}"

def get_ali_products(keyword):
    url = "https://api-sg.aliexpress.com/sync"
    params = {
        "app_key": ALI_APP_KEY, "timestamp": str(int(time.time() * 1000)), "sign_method": "sha256",
        "method": "aliexpress.affiliate.product.query", "partner_id": "apidoc", 
        "keywords": keyword, "page_size": "50", 
        "target_currency": "USD", "target_language": "EN", "tracking_id": ALI_TRACKING_ID
    }
    sorted_params = sorted(params.items())
    base_string = "".join([f"{k}{v}" for k, v in sorted_params])
    sign = hmac.new(ALI_SECRET.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    params["sign"] = sign
    try:
        response = requests.post(url, data=params, timeout=20)
        return response.json().get("aliexpress_affiliate_product_query_response", {}).get("resp_result", {}).get("result", {}).get("products", {}).get("product", [])
    except: return []

def generate_blog_content(product):
    # 제미나이 3.0 엔진을 사용하여 빠르게 대량 생성
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = f"Write a professional product review for: {product.get('product_title')}. Use Markdown."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=40)
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except: return None

def main():
    os.makedirs("_posts", exist_ok=True)
    
    # 🎯 중복 검사를 이번 실행(Session) 내에서만 하도록 대폭 완화합니다.
    current_session_ids = set()
    success_count = 0
    today_str = datetime.now().strftime("%Y-%m-%d")

    print(f"🚀 Mission Start: Target 40 posts for {today_str}")

    # 🎯 40개가 채워질 때까지 무한 루프
    while success_count < 40:
        kw = get_random_keyword()
        print(f"🔍 Searching: {kw} (Current: {success_count}/40)")
        
        products = get_ali_products(kw)
        if not products:
            continue
        
        random.shuffle(products) # 검색 결과 내에서도 무작위성 부여
        
        for p in products:
            if success_count >= 40: break
            
            p_id = str(p.get('product_id'))
            
            # 이번 세션에서 중복만 피합니다 (SEO 노출 극대화 모드)
            if p_id in current_session_ids: continue
            
            content = generate_blog_content(p)
            if content:
                # 🖼️ 이미지 URL 최적화 (https: 강제 부여 및 엑박 방지)
                img_url = p.get('product_main_image_url', '')
                if img_url.startswith('//'): img_url = 'https:' + img_url
                
                # 📝 파일 저장 (파일명에 랜덤 숫자를 넣어 겹침 방지)
                file_path = f"_posts/{today_str}-{p_id}-{random.randint(100,999)}.md"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"---\nlayout: post\ntitle: \"{p['product_title']}\"\ndate: {today_str}\n---\n\n![Product Image]({img_url})\n\n{content}\n\n[🛒 Buy on AliExpress]({p.get('promotion_link')})")
                
                current_session_ids.add(p_id)
                success_count += 1
                print(f"   ✅ Success {success_count}/40: {p_id}")
                time.sleep(1) # 제미나이 프로 할당량을 고려한 매너 대기
            else:
                print(f"   ❌ AI Generation failed for {p_id}")

    print(f"🏁 Mission Completed! Total {success_count} posts created.")

if __name__ == "__main__":
    main()
