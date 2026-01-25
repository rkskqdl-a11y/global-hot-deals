import os

# 1. Modifiers (Adjectives) - 영어 수식어
modifiers = [
    "Best Budget", "Top Rated", "High Quality", "Portable", "Wireless", 
    "Bluetooth", "Gaming", "RGB", "Mechanical", "Silent", 
    "Heavy Duty", "Fast Charging", "Ultralight", "Waterproof", "Foldable", 
    "Type-C", "Magnetic", "Smart", "IoT", "Minimalist", 
    "Travel Friendly", "Professional", "Gift for Him", "Gift for Her", "Trending",
    "Xiaomi", "Lenovo", "Baseus", "Anker Style", "Must Have"
]

# 2. Products (Nouns) - 영어 제품명
products = [
    # Tech & Gadgets
    "Mechanical Keyboard", "Vertical Mouse", "Gaming Mouse", "Power Bank", "USB Hub",
    "GaN Charger", "Monitor Light Bar", "Monitor Arm", "Tablet Stand", "Laptop Stand",
    "Smartphone Gimbal", "Bluetooth Speaker", "TWS Earbuds", "Noise Cancelling Headphones",
    "Smart Watch", "Apple Watch Strap", "iPad Case", "NVMe SSD Enclosure", "USB Flash Drive",
    "Mini PC", "Portable Projector", "TV Stick", "Air Purifier", "Humidifier",
    "Robot Vacuum", "Cordless Vacuum", "Hair Dryer", "Electric Toothbrush", "Water Flosser",
    "Smart Scale", "Desk Fan", "Portable Monitor", "Nintendo Switch Accessories", "PS5 Stand",
    "Drone 4K", "Action Camera", "Dash Cam", "Security Camera", "Smart Doorbell",
    
    # Car Accessories
    "Car Vacuum Cleaner", "Tire Inflator", "Jump Starter", "OBD2 Scanner", "Car Wash Towel",
    "Car Organizer", "Car Phone Holder", "Wireless Car Charger", "Head Up Display", "Car Trash Bin",
    
    # Camping & Outdoor
    "Camping Chair", "Camping Table", "Camping Lantern", "LED Flashlight", "Camping Stove",
    "Titanium Cup", "Sleeping Bag", "Inflatable Mat", "Camping Tent", "Fishing Reel",
    "Fishing Rod", "Lure Set", "Trekking Poles", "Bicycle Light", "Bike Computer",
    "Tactical Backpack", "Survival Kit", "Multitool", "Pocket Knife", "Heated Vest",
    
    # Home & DIY
    "Cordless Drill", "Precision Screwdriver Set", "Laser Distance Meter", "Digital Caliper", 
    "Soldering Iron", "Glue Gun", "Motion Sensor Light", "Smart Bulb", "LED Strip Lights", 
    "Kitchen Scale", "Coffee Grinder", "Milk Frother", "Vegetable Chopper", "Silicone Utensils"
]

def make_keywords():
    keywords = []
    # Generate combinations
    for mod in modifiers:
        for prod in products:
            keywords.append(f"{mod} {prod}")
    
    # Save to file
    with open("keywords.txt", "w", encoding="utf-8") as f:
        for k in keywords:
            f.write(k + "\n")
            
    print(f"✅ {len(keywords)} English keywords generated in keywords.txt")

if __name__ == "__main__":
    make_keywords()
