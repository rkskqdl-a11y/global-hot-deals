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

# 2. 폭탄급 키워드 뱅크 (상품 고갈 방지)
def get_mega_keywords():
    categories = [
        "Tech", "Home", "Kitchen", "Office", "Outdoor", "Gaming", "Health", "Car", "Tool", "Gift",
        "Beauty", "Pet", "Baby", "Security", "Audio", "Light", "DIY", "Smart", "Mobile", "PC"
    ]
    modifiers = ["Best", "Top", "New", "Cool", "Cheap", "Must-buy", "Popular", "Trending"]
    return [f"{m} {c}" for m in modifiers for c in categories]

def get_ali_products(keyword):
    url = "https://api-sg.aliexpress.com/sync"
    params = {
        "app_key": ALI_APP_KEY, "timestamp": str(int(time.time() * 1000)), "sign_method": "sha256",
        "method": "aliexpress.affiliate.product.query", "partner_id": "apidoc", "keywords": keyword,
        "target_currency": "USD", "target_language": "EN", "tracking_id": ALI_TRACKING_ID, "page_size": "50"
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
    # 제미나이 3.0 Flash는 빠르고 정확합니다.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt_text = (f"Write a review for: {product.get('product_title')}. "
                   f"Price: ${product.get('target_sale_price')}. Write in Markdown.")
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=40)
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except: return None

def main():
    os.makedirs("_posts", exist_ok=True)
    posted_ids = set()
    if os.path.exists("posted_ids.txt"):
        with open("posted_ids.txt", "r") as f:
            posted_ids = set(line.strip() for line in f)

    all_keywords = get_mega_keywords()
    random.shuffle(all_keywords)
    
    success_count = 0
    # 🎯 40개 채울 때까지 전진!
    for kw in all_keywords:
        if success_count >= 40: break
        
        print(f"🔍 Searching: {kw} (Target: 40, Current: {success_count})")
        products = get_ali_products(kw)
        
        inner_count = 0
        for p in products:
            if success_count >= 40 or inner_count >= 10: break # 키워드당 최대 10개까지 추출
            
            p_id = str(p.get('product_id'))
            if p_id in posted_ids: continue
            
            content = generate_blog_content(p)
            if content:
                today = datetime.now().strftime("%Y-%m-%d")
                # 🖼️ 이미지 URL 최적화 (https: 부여)
                img_url = p.get('product_main_image_url', '')
                if img_url.startswith('//'): img_url = 'https:' + img_url
                
                full_markdown = f"---\nlayout: post\ntitle: \"{p['product_title']}\"\ndate: {today}\n---\n\n![Image]({img_url})\n\n{content}\n\n[Check on AliExpress]({p.get('promotion_link')})"
                
                with open(f"_posts/{today}-{p_id}.md", "w", encoding="utf-8") as f:
                    f.write(full_markdown)
                with open("posted_ids.txt", "a") as f:
                    f.write(f"{p_id}\n")
                
                posted_ids.add(p_id)
                success_count += 1
                inner_count += 1
                print(f"✅ Success ({success_count}/40): {p_id}")
                time.sleep(2) # ⚡ 제미나이 프로 할당량 활용을 위해 휴식 단축
    
    print(f"🏁 Mission Done: {success_count} posts created.")

if __name__ == "__main__":
    main()
