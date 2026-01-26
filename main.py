import os
import time
import random
import hmac
import hashlib
import requests
import json
from datetime import datetime

# [환경 변수 설정 부분 동일]
ALI_APP_KEY = os.environ.get("ALI_APP_KEY", "").strip()
ALI_SECRET = os.environ.get("ALI_SECRET", "").strip()
ALI_TRACKING_ID = os.environ.get("ALI_TRACKING_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

def get_ali_products_by_category():
    # 🎯 인기 카테고리 ID 리스트
    category_ids = ["502", "44", "7", "509", "1501", "1503", "18", "1511"]
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
        return response.json().get("aliexpress_affiliate_product_query_response", {}).get("resp_result", {}).get("result", {}).get("products", {}).get("product", [])
    except: return []

def generate_blog_content(product):
    # 🎯 제미나이 1.5 플래시 (가장 빠르고 안정적)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = f"Write a simple 3-sentence review for: {product.get('product_title')}. Price: ${product.get('target_sale_price')}. Use Markdown."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        # 할당량 초과 시 60초 휴식 (어제 약속드린 부분)
        if "quota" in str(res_json).lower() or "429" in str(res_json):
            print("   ⏳ API Quota hit. Waiting 60s...")
            time.sleep(60)
    except: pass
    return None

def main():
    os.makedirs("_posts", exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_session_ids = set()
    success_count = 0
    
    print(f"🚀 Mission Start: Target 40 Posts (Image Fix Applied)")

    while success_count < 40:
        products = get_ali_products_by_category()
        if not products: continue
            
        for p in products:
            if success_count >= 40: break
            p_id = str(p.get('product_id'))
            if p_id in current_session_ids: continue
            
            content = generate_blog_content(p)
            
            # ✅ AI가 답을 안 해도 제목+가격만으로 포스팅 생성 (0개 방지)
            if not content:
                content = f"Check this out: {p.get('product_title')} for only ${p.get('target_sale_price')}!"
            
            # 🖼️ 이미지 URL 정밀 가공
            img_url = p.get('product_main_image_url', '').strip()
            if img_url:
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif not img_url.startswith('http'):
                    img_url = 'https://' + img_url
            else:
                # 이미지가 아예 없는 경우를 위한 대체 이미지 (예비용)
                img_url = "https://via.placeholder.com/500x500?text=No+Image+Available"

            file_path = f"_posts/{today_str}-{p_id}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                # 📝 Jekyll 포스트 규격에 맞게 작성
                f.write(f"---\nlayout: post\ntitle: \"{p['product_title']}\"\ndate: {today_str}\n---\n\n"
                        f"![Product Image]({img_url})\n\n" # 이미지 삽입
                        f"{content}\n\n"
                        f"### [🛒 Buy on AliExpress]({p.get('promotion_link')})") # 구매 링크
            
            current_session_ids.add(p_id)
            success_count += 1
            print(f"   ✅ SUCCESS ({success_count}/40): {p_id}")
            time.sleep(3) # 요청 간격을 넓혀 API를 보호합니다.

    print(f"🏁 Mission Completed: 40 posts created.")

if __name__ == "__main__":
    main()
