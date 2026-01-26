import os
import time
import random
import hmac
import hashlib
import requests
import json
from datetime import datetime

# [환경 변수 설정 - 사용자 정보 기반]
ALI_APP_KEY = os.environ.get("ALI_APP_KEY", "").strip()
ALI_SECRET = os.environ.get("ALI_SECRET", "").strip()
ALI_TRACKING_ID = os.environ.get("ALI_TRACKING_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

def get_huge_keyword_pool():
    # 💥 더 광범위한 검색을 위해 품목을 수백 개 단위로 확장 가능하도록 구성
    base = ["Smart", "Mini", "Portable", "Wireless", "Home", "Office", "Car", "Outdoor", "Kitchen", "Tech"]
    items = ["Gadget", "Tool", "Electronics", "Adapter", "Sensor", "Light", "Charger", "Fan", "Hub", "Case", "Stand", "Speaker", "Camera"]
    return [f"{b} {i}" for b in base for i in items]

def get_ali_products(keyword):
    url = "https://api-sg.aliexpress.com/sync"
    # 🎯 정렬 방식을 랜덤하게 섞어 매번 다른 상품이 상단에 나오게 유도
    sort_methods = ["SALE_PRICE_ASC", "SALE_PRICE_DESC", "LAST_VOLUME_DESC", "VOLUME_DESC"]
    params = {
        "app_key": ALI_APP_KEY, "timestamp": str(int(time.time() * 1000)), "sign_method": "sha256",
        "method": "aliexpress.affiliate.product.query", "keywords": keyword, "page_size": "50",
        "sort": random.choice(sort_methods), # 👈 매번 다른 순서로 검색
        "target_currency": "USD", "target_language": "EN", "tracking_id": ALI_TRACKING_ID
    }
    # [서명 생성 로직 동일]
    sorted_params = sorted(params.items())
    base_string = "".join([f"{k}{v}" for k, v in sorted_params])
    sign = hmac.new(ALI_SECRET.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    params["sign"] = sign
    try:
        response = requests.post(url, data=params, timeout=25)
        return response.json().get("aliexpress_affiliate_product_query_response", {}).get("resp_result", {}).get("result", {}).get("products", {}).get("product", [])
    except: return []

def generate_blog_content(product):
    # 🎯 제미나이 1.5 플래시 사용 (가장 빠르고 거절이 적음)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = f"Review this: {product.get('product_title')}. Price: ${product.get('target_sale_price')}. 5 sentences, Markdown."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=40)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        
        # 🚨 할당량 초과 시 '60초 휴식'을 '30초'로 줄여서 속도 향상 시도
        if "quota" in str(res_json).lower():
            print("   ⏳ Quota limit. Resting 30s...")
            time.sleep(30)
    except: pass
    return None

def main():
    os.makedirs("_posts", exist_ok=True)
    posted_ids = set()
    if os.path.exists("posted_ids.txt"):
        with open("posted_ids.txt", "r") as f:
            posted_ids = set(line.strip() for line in f)

    success_count = 0
    keywords = get_huge_keyword_pool()
    random.shuffle(keywords)

    print(f"🚀 Mission Start: 40 Posts Target")

    for kw in keywords:
        if success_count >= 40: break
        
        print(f"🔄 Searching: {kw}...")
        products = get_ali_products(kw)
        
        # 🎯 검색된 50개 상품 중 중복이 아닌 것을 "전부" 시도합니다.
        for p in products:
            if success_count >= 40: break
            p_id = str(p.get('product_id'))
            
            # 🛑 이미 올린 상품만 아니면 무조건 진행!
            if p_id in posted_ids: continue
            
            content = generate_blog_content(p)
            if content:
                today = datetime.now().strftime("%Y-%m-%d")
                img = p.get('product_main_image_url', '').replace('//', 'https://') if p.get('product_main_image_url') else ""
                
                with open(f"_posts/{today}-{p_id}.md", "w", encoding="utf-8") as f:
                    f.write(f"---\nlayout: post\ntitle: \"{p['product_title']}\"\ndate: {today}\n---\n\n![Image]({img})\n\n{content}\n\n[🛒 Buy Link]({p.get('promotion_link')})")
                
                with open("posted_ids.txt", "a") as f: f.write(f"{p_id}\n")
                posted_ids.add(p_id)
                success_count += 1
                print(f"   ✨ Created ({success_count}/40): {p_id}")
                time.sleep(2) # ⚡ 딜레이 최소화
            else:
                # 생성 실패 시에도 다음 상품으로 즉시 이동하여 '고갈' 방지
                continue

    print(f"🏁 Mission Completed: {success_count} posts.")

if __name__ == "__main__":
    main()
