import requests
import json
import os
import random
import re
from datetime import datetime, timedelta
from faker import Faker

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
fake = Faker()

BRANDS = [
    "Lumina", "ApexGear", "NovaTech", "Vanguard", "Essential Goods",
    "Urbanite", "EcoLife", "Zenith", "Pioneer", "Daily Basics", 
    "Aura", "Prism", "Global Direct", "Studio 99", "Peak Performance", 
    "NeoStyle", "Artisana", "EliteCraft", "Creative Den", "Signature Supply"
]

ADJECTIVES = [
    "Premium", "Modern", "Minimalist", "Versatile", "Rugged",
    "Urban", "Classic", "Vibrant", "Sleek", "Ergonomic",
    "High-Performance", "Lightweight", "Durable", "Compact", "Dynamic",
    "Retro", "Futuristic", "Elegant", "Bold", "Everyday"
]

MATERIALS = [
    "Genuine Leather", "Organic Cotton", "Carbon Fiber",
    "Stainless Steel", "Recycled Polyester", "Bamboo Fiber", 
    "Brushed Metal", "Tempered Glass", "Sustainable Wood", 
    "Nylon Canvas", "Premium Denim", "Aerospace Aluminum"
]

def generate_hybrid_data(target_products=100000, target_customers=20000, target_reviews=60000):
    print("=== Phase 13.A: Fetching Real Scaffolding ===")
    url = "https://dummyjson.com/products?limit=100"
    response = requests.get(url)
    raw_data = response.json().get("products", [])

    categories_map = {}
    base_products = []
    base_comments = []

    cat_id_counter = 1
    for item in raw_data:
        cname = item.get("category", "Uncategorized").capitalize()
        if cname not in categories_map:
            categories_map[cname] = cat_id_counter
            cat_id_counter += 1
        
        desc = re.sub('<[^<]+?>', '', item.get("description", "")).replace('\n', ' ').replace('\r', '')
        img_url = item.get("images", [None])[0] if item.get("images") else item.get("thumbnail", "")

        base_products.append({
            "category_id": categories_map[cname],
            "title": item.get("title", "Product"),
            "price": float(item.get("price", 0.0)),
            "width": float(item.get("dimensions", {}).get("width", 10.0)),
            "height": float(item.get("dimensions", {}).get("height", 10.0)),
            "desc": desc,
            "image": img_url,
            "thumbnail": item.get("thumbnail", "")
        })

        for rev in item.get("reviews", []):
            if rev.get("comment"):
                base_comments.append((int(rev.get("rating", 3)), rev.get("comment")))

    print("=== Phase 13.B: Foreign Key & Relationship Synthesis ===")
    
    # Write Categories
    print("-> Writing Categories...")
    with open(os.path.join(DATA_DIR, "categories.jsonl"), "w") as f:
        for name, cid in categories_map.items():
            f.write(json.dumps({"id": cid, "name": name}) + '\n')

    # Synthesize Products
    print(f"-> Combinatorial Escalation: {target_products} Products...")
    products_price_map = {}
    with open(os.path.join(DATA_DIR, "products.jsonl"), "w") as f:
        for pid in range(1, target_products + 1):
            random.seed(pid)
            bp = base_products[pid % len(base_products)]
            br = random.choice(BRANDS)
            adj = random.choice(ADJECTIVES)
            mat = random.choice(MATERIALS)
            
            ref = f"{br} {adj} {bp['title']} ({mat} Edition)"
            enrich_desc = f"{bp['desc']} It is masterfully crafted from {mat} by {br}."
            
            p_obj = {
                "id": pid,
                "category_id": bp['category_id'],
                "reference": ref,
                "price": bp['price'],
                "stock": random.randint(0, 150),
                "width": bp['width'],
                "height": bp['height'],
                "description": enrich_desc,
                "image": bp['image'],
                "thumbnail": bp['thumbnail']
            }
            products_price_map[pid] = bp['price']
            f.write(json.dumps(p_obj) + '\n')

    # Synthesize Customers
    print(f"-> Reverse-Synthesize: {target_customers} Customers...")
    Faker.seed(42)
    with open(os.path.join(DATA_DIR, "customers.jsonl"), "w") as f:
        for cid in range(1, target_customers + 1):
            c_obj = {
                "id": cid,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.email(),
                "address": fake.street_address(),
                "city": fake.city(),
                "zipcode": fake.postcode(),
                "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={cid}",
                "birthday": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
                "nb_commands": 0,
                "total_spent": 0.0
            }
            f.write(json.dumps(c_obj) + '\n')

    # Synthesize Temporal Orders and Reviews
    print(f"-> Temporal Synthesis: {target_reviews} Orders, Invoices & Reviews...")
    with open(os.path.join(DATA_DIR, "reviews.jsonl"), "w") as fr, \
         open(os.path.join(DATA_DIR, "orders.jsonl"), "w") as fo, \
         open(os.path.join(DATA_DIR, "invoices.jsonl"), "w") as fi:
         
        for rid in range(1, target_reviews + 1):
            random.seed(rid)
            rev_date = fake.date_between(start_date='-2y', end_date='today')
            # Order happens strictly BEFORE review
            ord_date = rev_date - timedelta(days=random.randint(5, 20))
            
            cid = random.randint(1, target_customers)
            pid = random.randint(1, target_products)
            price = products_price_map[pid]
            
            rating, comment = random.choice(base_comments) if base_comments else (4, "Excellent quality.")
            
            r_obj = {
                "id": rid,
                "date": rev_date.isoformat() + "T10:00:00.000Z",
                "customer_id": cid,
                "product_id": pid,
                "rating": rating,
                "comment": comment,
                "status": "published"
            }
            
            qty = random.randint(1, 3)
            tot = round(price * qty, 2)
            
            o_obj = {
                "id": rid, # Simple 1:1 coupling for schema
                "date": ord_date.isoformat() + "T10:00:00.000Z",
                "customer_id": cid,
                "total": tot,
                "status": "delivered",
                "returned": False,
                "basket": [{"product_id": pid, "quantity": qty}]
            }
            
            i_obj = {
                "id": rid,
                "date": ord_date.isoformat() + "T14:00:00.000Z",
                "order_id": rid,
                "customer_id": cid,
                "total": tot
            }
            
            fr.write(json.dumps(r_obj) + '\n')
            fo.write(json.dumps(o_obj) + '\n')
            fi.write(json.dumps(i_obj) + '\n')

    print("=== Pipeline Complete: All JSONL Artifacts Successfully Generated ===")

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    data_scale = int(os.getenv("DATA_SCALE", "100000"))
    customers = max(1, data_scale // 5)
    reviews = max(1, int(data_scale * 0.6))
    
    print(f"🌍 [ENV DATA_SCALE TRIGGERED] Targets -> Products: {data_scale}, Customers: {customers}, Reviews: {reviews}")
    
    generate_hybrid_data(target_products=data_scale, target_customers=customers, target_reviews=reviews)
