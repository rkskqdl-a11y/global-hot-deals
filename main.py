import os
import time
import random
import hmac
import hashlib
import requests
import json
from datetime import datetime

# 1. 환경 변수 로드
ALI_APP_KEY = os.environ.get("ALI_APP_KEY", "").strip()
ALI_SECRET = os.environ.get("ALI_SECRET", "").strip()
ALI_TRACKING_ID = os.environ.get("ALI_TRACKING_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

if ALI_SECRET:
    print(f"✅ 비밀키 로드 성공 (길이: {len(ALI_SECRET)})")

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
        "page_size": "5"
    }
    
    sorted_params = sorted(params.items())
    base_string = "".join([f"{k}{v}" for k, v in sorted_params])
    sign = hmac.new(ALI_SECRET.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    params["sign"] = sign
    
    try:
        response = requests.post(url, data=params)
        data = response.json()
        if "aliexpress_affiliate_product_query_response" in data:
            result = data["aliexpress_affiliate_product_query_response"]["resp_result"]["result"]
            return result["products"]["product"]
        return []
    except:
        return []

def generate_blog_content(product):
    # 모델 경로를 v1으로, 모델명을 gemini-1.5-flash로 명확히 지정
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    prompt_text = f"Review this product in English: {product.get('product_title')}. Price: ${product.get('target_sale_price')}. Use Markdown."
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    
    try:
        # v1 경로로 시도
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        # 만약 v1에서 실패하면 v1beta로 재시도 (안전장치)
        if "error" in result:
            url_beta = url.replace("/v1/", "/v1beta/")
            response = requests.post(url_beta, headers=headers, json=payload)
            result = response.json()

        if "candidates" in result:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        print(f"❌ Gemini API Error: {result.get('error', {}).get('message')}")
        return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def main():
    try:
        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]
    except: return

    target_keyword = random.choice(keywords)
    print(f"🎯 Target Keyword: {target_keyword}")

    products = get_ali_products(target_keyword)
    if not products:
        print("❌ 상품 검색 실패")
        return

    selected_product = products[0] # 첫 번째 상품 선택
    print(f"📝 글 작성 중: {selected_product['product_title'][:30]}...")
    content = generate_blog_content(selected_product)
    
    if content:
        today_str = datetime.now().strftime("%Y-%m-%d")
        os.makedirs("posts", exist_ok=True)
        file_name = f"posts/{today_str}-post.md"
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"---\ntitle: {selected_product['product_title']}\n---\n\n{content}\n\n[Buy Now]({selected_product['promotion_link']})")
        
        print(f"🎉 포스팅 완료: {file_name}")

if __name__ == "__main__":
    main()
