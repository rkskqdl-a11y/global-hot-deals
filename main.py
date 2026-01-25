import os
import json
import time
import random
import hashlib
import hmac
import requests
import google.generativeai as genai
from datetime import datetime

# 1. Load Environment Variables
ALI_APP_KEY = os.environ.get("ALI_APP_KEY")
ALI_SECRET = os.environ.get("ALI_SECRET") # or ALI_APP_SECRET based on your setting
ALI_TRACKING_ID = os.environ.get("ALI_TRACKING_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_ali_products(keyword):
    url = "https://api-sg.aliexpress.com/sync"
    
    # Parameters for Global (English/USD)
    sys_params = {
        "app_key": ALI_APP_KEY,
        "timestamp": str(int(time.time() * 1000)),
        "sign_method": "sha256",
        "method": "aliexpress.affiliate.product.query",
    }
    biz_params = {
        "keywords": keyword,
        "target_currency": "USD",       # Changed to USD
        "target_language": "EN",        # Target Language English
        "sort": "LAST_VOLUME_DESC",
        "tracking_id": ALI_TRACKING_ID,
        "page_size": "5"
    }
    
    all_params = {**sys_params, **biz_params}
    
    # Generate Signature (IOP)
    sorted_items = sorted(all_params.items())
    base_string = ""
    for k, v in sorted_items:
        base_string += k + v
        
    sign = hmac.new(ALI_SECRET.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    all_params["sign"] = sign
    
    try:
        response = requests.post(url, data=all_params)
        data = response.json()
        
        if "aliexpress_affiliate_product_query_response" in data:
            return data["aliexpress_affiliate_product_query_response"]["resp_result"]["result"]["products"]["product"]
        else:
            print(f"API Error: {data}")
            return []
    except Exception as e:
        print(f"Request Error: {e}")
        return []

def generate_blog_content(product):
    # Prompt for English Content
    prompt = f"""
    You are a professional tech and lifestyle gadget reviewer. Write a compelling blog post in English based on the AliExpress product details below.
    
    [Product Info]
    - Product Name: {product.get('product_title')}
    - Price: ${product.get('target_sale_price')} {product.get('target_sale_price_currency')}
    - Rating: {product.get('evaluate_rate')}
    - Image URL: {product.get('product_main_image_url')}
    
    [Requirements]
    1. Title: Catchy and SEO-friendly (e.g., "Why You Need This...", "Best Budget...").
    2. Body: Explain the key features, pros, and why it's a good deal. Use a friendly, enthusiastic tone.
    3. Structure: Use Markdown (Headings, Bullet points).
    4. Language: English only.
    5. Conclusion: A strong call to action to check the price.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def main():
    # 1. Load Keywords
    try:
        with open("keywords.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("keywords.txt not found.")
        return

    if not keywords:
        print("No keywords found.")
        return

    target_keyword = random.choice(keywords)
    print(f"Target Keyword: {target_keyword}")

    # 2. Search Products
    products = get_ali_products(target_keyword)
    if not products:
        print("No products found.")
        return

    # 3. Check Duplicates
    posted_ids = set()
    if os.path.exists("posted_ids.txt"):
        with open("posted_ids.txt", "r") as f:
            posted_ids = set(line.strip() for line in f)

    selected_product = None
    for p in products:
        p_id = str(p['product_id'])
        if p_id not in posted_ids:
            selected_product = p
            break
    
    if not selected_product:
        print("All products in this search are already posted.")
        return

    # 4. Generate Content
    print(f"Selected Product: {selected_product['product_title']}")
    content = generate_blog_content(selected_product)
    
    if not content:
        print("Failed to generate content.")
        return

    # 5. Save File
    today_str = datetime.now().strftime("%Y-%m-%d")
    # File name formatting for English title
    clean_title = "".join([c if c.isalnum() else "_" for c in selected_product['product_title'][:30]])
    file_name = f"posts/{today_str}-{clean_title}.md"
    
    os.makedirs("posts", exist_ok=True)
    
    affiliate_link = selected_product['promotion_link']
    
    # English Disclaimer & Layout
    final_content = f"""---
title: "{selected_product['product_title']}"
date: {today_str}
---

{content}

<br>

### 👇 Check the Best Price Here
**[>> Buy Now on AliExpress]({affiliate_link})**

<br>
<br>

> **Disclaimer:** This post contains affiliate links. If you make a purchase through these links, we may earn a commission at no extra cost to you.
"""

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print(f"Post created: {file_name}")

    # 6. Record ID
    with open("posted_ids.txt", "a") as f:
        f.write(f"{selected_product['product_id']}\n")

if __name__ == "__main__":
    main()
