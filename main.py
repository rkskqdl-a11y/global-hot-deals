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

def get_ali_products_by_category():
    # 🎯 키워드 대신 알리익스프레스의 대형 카테고리 ID를 사용하여 상품을 확실히 가져옵니다.
    # 502(가전), 44(자동차), 7(컴퓨터), 509(폰), 1501(베이비) 등
    category_ids = ["502", "44", "7", "509", "1501", "1503", "18", "1511", "200003406"]
    cat_id = random.choice(category_ids)
    
    url = "https://api-sg.aliexpress.com/sync"
    params = {
        "app_key": ALI_APP_KEY, "timestamp": str(int(time.time() * 1000)), "sign_method": "sha256",
        "method": "aliexpress.affiliate.product.query", "category_ids": cat_id, 
        "page_size": "50", "target_currency": "USD", "target_language": "EN", "tracking_id": ALI_TRACKING_ID
    }
    # [서명 생성 로직]
    sorted_params = sorted(params.items())
    base_string = "".join([f"{k}{v}" for k, v in sorted_params])
    sign = hmac.new(ALI_SECRET.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    params["sign"] = sign
    
    try:
        response = requests.post(url, data=params, timeout=20)
        data = response.json()
        products = data.get("aliexpress_affiliate_product_query_response", {}).get("resp_result", {}).get("result", {}).get("products", {}).get("product", [])
        print(f"📡 Category {cat_id} Search: Found {len(products)} products.") # 👈 검색 결과 로그 추가
        return products
    except Exception as e:
        print(f"📡 API Error: {e}")
        return []

def generate_blog_content(product):
    # 🎯 제미나이 1.5 플래시 사용
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = f"Write a simple 3-sentence review for: {product.get('product_title')}. Price: ${product.get('target_sale_price')}. Markdown format."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        
        # 🚨 할당량 초과 시 30초 대기
        if "429" in str(res_json) or "quota" in str(res_json).lower():
            print("   ⏳ AI Quota hit. Waiting 30s...")
            time.sleep(30)
    except: pass
    return None # 실패 시 None 리턴

def main():
    os.makedirs("_posts", exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_session_ids = set()
    success_count = 0
    
    print(f"🚀 Mission Start: Target 40 Posts for {today_str}")

    # 🎯 40개가 채워질 때까지 끝까지 반복합니다.
    while success_count < 40:
        products = get_ali_products_by_category()
        
        if not products:
            print("   ⚠️ No products found in this category. Retrying...")
            time.sleep(5)
            continue
            
        for p in products:
            if success_count >= 40: break
            
            p_id = str(p.get('product_id'))
            if p_id in current_session_ids: continue
            
            content = generate_blog_content(p)
            
            # 🛡️ AI 생성 실패 시 '기본 텍스트'로라도 발행 (0개 방지 전략)
            if not content:
                print(f"   ⚠️ AI Review failed for {p_id}. Using fallback text.")
                content = f"Check out this amazing product: {p.get('product_title')}. Great value for only ${p.get('target_sale_price')}!"
            
            img_url = p.get('product_main_image_url', '').replace('//', 'https://')
            file_path = f"_posts/{today_str}-{p_id}.md"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"---\nlayout: post\ntitle: \"{p['product_title']}\"\ndate: {today_str}\n---\n\n![Image]({img_url})\n\n{content}\n\n[🛒 Buy on AliExpress]({p.get('promotion_link')})")
            
            current_session_ids.add(p_id)
            success_count += 1
            print(f"   ✅ SUCCESS ({success_count}/40): {p_id}")
            time.sleep(2) # ⚡ 안정적인 처리를 위한 최소 대기

    print(f"🏁 Mission Completed: {success_count} posts created.")

if __name__ == "__main__":
    main()
