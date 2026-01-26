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

def get_ali_products():
    # 다양한 카테고리에서 상품 수집
    cat_id = random.choice(["502", "44", "7", "509", "1501", "1503", "18", "1511"])
    url = "https://api-sg.aliexpress.com/sync"
    params = {
        "app_key": ALI_APP_KEY, "timestamp": str(int(time.time() * 1000)), "sign_method": "sha256",
        "method": "aliexpress.affiliate.product.query", "category_ids": cat_id, 
        "page_size": "50", "target_currency": "USD", "target_language": "EN", "tracking_id": ALI_TRACKING_ID
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
    # 안정적인 1.5 Flash 모델 사용
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = f"Write a professional product review for: {product.get('product_title')}. Price: ${product.get('target_sale_price')}. Use Markdown."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=40)
        res_json = response.json()
        if "candidates" in res_json:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        # 할당량 초과 시 60초 휴식
        if "quota" in str(res_json).lower() or "429" in str(res_json):
            print("   ⏳ API Quota full. Waiting 60s...")
            time.sleep(60)
    except: pass
    return None

def main():
    os.makedirs("_posts", exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_session_ids = set()
    success_count = 0
    
    # ✅ 법적 고지 문구 (공정위 가이드라인 준수)
    disclosure_text = "> **고지사항:** 이 포스팅은 알리익스프레스 어필리에이트 활동의 일환으로, 구매 시 이에 따른 일정액의 수수료를 제공받을 수 있습니다.\n\n"

    print(f"🚀 Mission: 40 Posts (Image & Disclosure Fix)")

    while success_count < 40:
        products = get_ali_products()
        if not products: continue
            
        for p in products:
            if success_count >= 40: break
            p_id = str(p.get('product_id'))
            if p_id in current_session_ids: continue
            
            # 🖼️ 이미지 URL HTTPS 강제 교정
            img_url = p.get('product_main_image_url', '').strip()
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url and not img_url.startswith('http'):
                img_url = 'https://' + img_url
            
            # 파라미터 제거로 이미지 로딩 최적화
            img_url = img_url.split('?')[0] if '?' in img_url else img_url

            content = generate_blog_content(p)
            if not content:
                content = f"Check out this amazing {p.get('product_title')} on AliExpress for just ${p.get('target_sale_price')}!"

            # ✅ 에러 수정된 부분: f"..." 형식 사용
            file_path = f"_posts/{today_str}-{p_id}.md"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"---\nlayout: post\ntitle: \"{p['product_title']}\"\ndate: {today_str}\n---\n\n"
                        f"{disclosure_text}" # 고지 문구
                        f"![Product Image]({img_url})\n\n" # 이미지
                        f"{content}\n\n" # 본문
                        f"### [🛒 Buy on AliExpress]({p.get('promotion_link')})") # 버튼
            
            current_session_ids.add(p_id)
            success_count += 1
            print(f"   ✅ SUCCESS ({success_count}/40): {p_id}")
            time.sleep(5) # API 안정성을 위한 대기

    print(f"🏁 Mission Completed: 40 posts created.")

if __name__ == "__main__":
    main()
