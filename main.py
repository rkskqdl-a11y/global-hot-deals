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

def get_massive_keyword_list():
    modifiers = ["Best Budget", "Top Rated", "High Quality", "Portable", "Wireless", "Gaming", "Waterproof", "Smart", "Gift for Him", "Trending", "Must Have"]
    products = ["Mechanical Keyboard", "Gaming Mouse", "Power Bank", "USB Hub", "GaN Charger", "Smart Watch", "Mini PC", "Portable Projector", "Robot Vacuum", "Camping Lantern", "Pocket Knife"]
    return [f"{m} {p}" for m in modifiers for p in products]

def get_ali_products(keyword):
    url = "https://api-sg.aliexpress.com/sync"
    params = {
        "app_key": ALI_APP_KEY, "timestamp": str(int(time.time() * 1000)), "sign_method": "sha256",
        "method": "aliexpress.affiliate.product.query", "partner_id": "apidoc", "keywords": keyword,
        "target_currency": "USD", "target_language": "EN", "tracking_id": ALI_TRACKING_ID, "page_size": "5"
    }
    sorted_params = sorted(params.items())
    base_string = "".join([f"{k}{v}" for k, v in sorted_params])
    sign = hmac.new(ALI_SECRET.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    params["sign"] = sign
    try:
        response = requests.post(url, data=params)
        return response.json().get("aliexpress_affiliate_product_query_response", {}).get("resp_result", {}).get("result", {}).get("products", {}).get("product", [])
    except: return []

def generate_blog_content(product):
    # 🚀 제미나이 3.0 지능을 활용하기 위한 다중 경로 시도
    # v1(정식) 경로를 우선 시도하여 404 에러를 방지합니다.
    endpoints = [
        "https://generativelanguage.googleapis.com/v1/models/gemini-3.0-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.0-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    ]
    
    headers = {'Content-Type': 'application/json'}
    # 제미나이 3.0의 Thinking 능력을 자극하는 프롬프트
    prompt_text = (f"Review this product using your Gemini 3.0 advanced reasoning: {product.get('product_title')}. "
                   f"Price: ${product.get('target_sale_price')}. "
                   f"Write a persuasive, SEO-friendly English review in Markdown.")
    
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    
    for url in endpoints:
        try:
            full_url = f"{url}?key={GEMINI_API_KEY}"
            response = requests.post(full_url, headers=headers, json=payload, timeout=10)
            result = response.json()
            
            if "candidates" in result:
                print(f"✅ Success using endpoint: {url}")
                return result["candidates"][0]["content"]["parts"][0]["text"]
            
            print(f"ℹ️ Endpoint {url} skipped: {result.get('error', {}).get('message', 'Unknown error')}")
        except Exception as e:
            print(f"ℹ️ Connection to {url} failed: {e}")
            continue
            
    return None

def main():
    os.makedirs("posts", exist_ok=True)
    if not os.path.exists("posted_ids.txt"):
        with open("posted_ids.txt", "w") as f: f.write("")

    all_keywords = get_massive_keyword_list()
    target_keyword = random.choice(all_keywords)
    print(f"📚 Total Keywords: {len(all_keywords)} | 🎯 Target: {target_keyword}")

    products = get_ali_products(target_keyword)
    if not products:
        print("❌ AliExpress No Products Found.")
        return

    selected_product = products[0]
    print(f"📝 Writing Review with Gemini 3.0 Intelligence: {selected_product['product_title'][:40]}...")
    content = generate_blog_content(selected_product)
    
    if content:
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = f"posts/{today}-{selected_product.get('product_id')}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        with open("posted_ids.txt", "a") as f:
            f.write(f"{selected_product.get('product_id')}\n")
        print(f"🎉 SUCCESS: {file_path} created!")
    else:
        print("❌ Content generation failed across all endpoints.")

if __name__ == "__main__":
    main()
