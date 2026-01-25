import os
import time
import random
import hmac
import hashlib
import requests
import json
import warnings
# 구글 경고 메시지 무시 설정
warnings.filterwarnings("ignore")
import google.generativeai as genai
from datetime import datetime

# 1. 환경 변수 로드 및 디버깅
ALI_APP_KEY = os.environ.get("ALI_APP_KEY")
ALI_SECRET = os.environ.get("ALI_SECRET")
ALI_TRACKING_ID = os.environ.get("ALI_TRACKING_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 비밀키가 제대로 로드되었는지 확인 (보안을 위해 앞자리만 출력)
if not ALI_SECRET:
    print("❌ 오류: ALI_SECRET이 비어있습니다. GitHub Secrets 설정을 확인하세요.")
else:
    print(f"✅ 비밀키 로드 성공 (길이: {len(ALI_SECRET)})")

# 2. Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_ali_products(keyword):
    url = "https://api-sg.aliexpress.com/sync"
    
    # 공통 파라미터 (IOP 규격)
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
    
    # 서명(Sign) 생성 - 공식 알고리즘 적용
    # 1. 파라미터 정렬
    sorted_params = sorted(params.items())
    
    # 2. 문자열 연결 (key+value)
    base_string = ""
    for k, v in sorted_params:
        base_string += str(k) + str(v)
    
    # 3. HMAC-SHA256 암호화
    sign = hmac.new(ALI_SECRET.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    params["sign"] = sign
    
    try:
        # POST 요청
        response = requests.post(url, data=params)
        data = response.json()
        
        # 에러 응답 확인
        if "error_response" in data:
            print(f"🚫 API 호출 실패: {data['error_response'].get('msg', '알 수 없는 오류')}")
            print(f"상세 내용: {data}")
            return []
            
        if "aliexpress_affiliate_product_query_response" in data:
            result = data["aliexpress_affiliate_product_query_response"]["resp_result"]["result"]
            if result and "products" in result:
                return result["products"]["product"]
        
        print("상품을 찾을 수 없습니다.")
        return []
        
    except Exception as e:
        print(f"Request Error: {e}")
        return []

def generate_blog_content(product):
    prompt = f"""
    You are a professional tech reviewer. Write a short, engaging blog post review in English for:
    Product: {product.get('product_title')}
    Price: ${product.get('target_sale_price')}
    Rating: {product.get('evaluate_rate')}
    Image: {product.get('product_main_image_url')}
    
    Format using Markdown. Include pros, features, and a conclusion.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def main():
    # 키워드 파일 읽기
    try:
        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]
    except:
        print("keywords.txt 파일이 없습니다.")
        return

    if not keywords:
        print("키워드가 없습니다.")
        return

    target_keyword = random.choice(keywords)
    print(f"🎯 Target Keyword: {target_keyword}")

    products = get_ali_products(target_keyword)
    
    if not products:
        print("❌ 상품 검색 실패 - 프로그램을 종료합니다.")
        return

    # 이미 올린 상품 제외
    posted_ids = set()
    if os.path.exists("posted_ids.txt"):
        with open("posted_ids.txt", "r") as f:
            posted_ids = set(line.strip() for line in f)

    selected_product = None
    for p in products:
        if str(p['product_id']) not in posted_ids:
            selected_product = p
            break
    
    if not selected_product:
        print("모든 상품이 이미 포스팅되었습니다.")
        return

    print(f"📝 글 작성 중: {selected_product['product_title'][:30]}...")
    content = generate_blog_content(selected_product)
    
    if content:
        today_str = datetime.now().strftime("%Y-%m-%d")
        clean_title = "".join([c if c.isalnum() else "_" for c in selected_product['product_title'][:30]])
        file_name = f"posts/{today_str}-{clean_title}.md"
        
        os.makedirs("posts", exist_ok=True)
        
        final_content = f"""---
title: "{selected_product['product_title']}"
date: {today_str}
---

{content}

<br>

### 👇 Check the Best Price Here
**[>> Buy Now on AliExpress]({selected_product['promotion_link']})**

<br>
> **Disclaimer:** This post contains affiliate links.
"""
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(final_content)
            
        with open("posted_ids.txt", "a") as f:
            f.write(f"{selected_product['product_id']}\n")
            
        print(f"🎉 포스팅 완료: {file_name}")

if __name__ == "__main__":
    main()
