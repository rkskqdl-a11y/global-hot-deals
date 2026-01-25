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
    modifiers = ["Best Budget", "Top Rated", "High Quality", "Portable", "Wireless", "Gaming", "Smart", "Gift"]
    products = ["Mechanical Keyboard", "Gaming Mouse", "Power Bank", "USB Hub", "GaN Charger", "Smart Watch", "Mini PC", "Projector", "Robot Vacuum", "Camping Lantern"]
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
    # 🚀 지난 로그에서 성공이 확인된 제미나이 3.0 모델을 1순위로 배치합니다.
    # 제미나이 3.0은 추론 능력이 뛰어나 마케팅 문구 작성에 최적입니다.
    candidates = [
        "models/gemini-3-flash-preview", 
        "models/gemini-1.5-flash-latest",
        "models/gemini-pro-latest"
    ]
    
    headers = {'Content-Type': 'application/json'}
    # 제미나이 3.0의 에이전트 능력을 자극하는 고급 프롬프트
    prompt_text = (f"Review this product using Gemini 3.0 reasoning: {product.get('product_title')}. "
                   f"Price: ${product.get('target_sale_price')}. Write an expert-level review in Markdown.")
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    
    for model_name in candidates:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            result = response.json()
            
            if "candidates" in result:
                print(f"✅ Success using model: {model_name}")
                return result["candidates"][0]["content"]["parts"][0]["text"]
            
            # 429 에러 발생 시 상세 이유 출력
            error_msg = result.get('error', {}).get('message', 'Unknown error')
            print(f"ℹ️ Model {model_name} skipped: {error_msg}")
            
            # 할당량 초과 시 잠시 대기 (구글 권장 사항)
            if "quota" in error_msg.lower():
                print("Waiting 10 seconds due to quota...")
                time.sleep(10)
                
        except Exception as e:
            print(f"ℹ️ Connection error with {model_name}: {e}")
            continue
    return None

def main():
    # 📂 웹사이트 대문에 목록이 뜨도록 반드시 '_posts' 폴더를 사용합니다.
    os.makedirs("_posts", exist_ok=True)
    if not os.path.exists("posted_ids.txt"):
        with open("posted_ids.txt", "w") as f: f.write("")

    all_keywords = get_massive_keyword_list()
    target = random.choice(all_keywords)
    print(f"🎯 Selected Target: {target}")

    products = get_ali_products(target)
    if not products:
        print("❌ No products found from AliExpress.")
        return

    selected_product = products[0]
    print(f"📝 Writing Review with Gemini 3.0: {selected_product['product_title'][:40]}...")
    
    content = generate_blog_content(selected_product)
    
    if content:
        today = datetime.now().strftime("%Y-%m-%d")
        # Jekyll 규격 파일명: YYYY-MM-DD-제목.md
        file_path = f"_posts/{today}-{selected_product.get('product_id')}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            # 제목과 날짜를 포함한 헤더(Front Matter) 추가
            f.write(f"---\ntitle: \"{selected_product['product_title']}\"\ndate: {today}\n---\n\n{content}")
        
        with open("posted_ids.txt", "a") as f:
            f.write(f"{selected_product.get('product_id')}\n")
        print(f"🎉 SUCCESS: {file_path} created!")
    else:
        print("❌ All Gemini models failed to generate content.")

if __name__ == "__main__":
    main()
