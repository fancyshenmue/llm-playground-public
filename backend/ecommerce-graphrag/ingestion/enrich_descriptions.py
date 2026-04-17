"""
Production-Grade Description Enrichment Script
================================================
Uses Gemini 2.5 Flash to generate realistic e-commerce product descriptions
for all 130 unique product references, then batch-updates PostgreSQL.

Cost: ~130 API calls ≈ $0.001 (negligible)
Time: ~2 minutes
"""
import os
import sys
import json
import asyncio
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))



import google.generativeai as genai
from core.database import get_postgres_pool

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.8})

ENRICHMENT_PROMPT = """You are an expert e-commerce copywriter. Generate a realistic, detailed product description for a poster/art print sold in an online store.

Product Name: {name}
Category: {category}

Requirements:
- Write 3-4 sentences (80-120 words)
- Include specific details such as: materials (e.g., premium matte paper, recycled canvas, UV-resistant ink), dimensions, artistic style, color palette
- Mention a brand name (invent a realistic one like "ArtVista", "FrameHaus", "PosterCraft", "WallSoul", etc.)
- Describe ideal usage scenarios (e.g., living room, office, nursery, café)
- Mention complementary products or collections
- Use professional e-commerce language with emotional appeal
- Do NOT use markdown formatting. Plain text only.

Output ONLY the product description text, nothing else."""

async def generate_description(name: str, category: str, semaphore: asyncio.Semaphore) -> tuple[str, str, str]:
    async with semaphore:
        prompt = ENRICHMENT_PROMPT.format(name=name, category=category)
        try:
            res = await model.generate_content_async(prompt)
            desc = res.text.strip()
            print(f"  ✓ [{category}] {name} ({len(desc)} chars)")
            return (name, category, desc)
        except Exception as e:
            print(f"  ✗ [{category}] {name}: {e}")
            return (name, category, f"A beautiful {category} poster featuring {name}.")

async def main():
    pool = get_postgres_pool()
    
    # Step 1: Get all 130 unique products
    print("=" * 60)
    print("PHASE 1: Reading unique product references from PostgreSQL")
    print("=" * 60)
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT p.reference, c.name 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                ORDER BY c.name, p.reference
            """)
            unique_products = [(row[0], row[1]) for row in cur.fetchall()]
    
    print(f"Found {len(unique_products)} unique product references across all categories.\n")
    
    # Step 2: Generate or load cached descriptions
    CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "enriched_descriptions.json")
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    if os.path.exists(CACHE_FILE):
        print("=" * 60)
        print("PHASE 2: Loading cached descriptions (no API calls needed)")
        print("=" * 60)
        with open(CACHE_FILE, "r") as f:
            cached = json.load(f)
        results = [(item["name"], item["category"], item["description"]) for item in cached]
        print(f"\n✓ Loaded {len(results)} descriptions from cache: {CACHE_FILE}\n")
    else:
        print("=" * 60)
        print("PHASE 2: Generating production-grade descriptions via Gemini 2.5 Flash")
        print("         (First run only — results will be cached for future use)")
        print("=" * 60)
        
        semaphore = asyncio.Semaphore(10)  # 10 concurrent API calls
        start_time = time.time()
        
        tasks = [generate_description(name, cat, semaphore) for name, cat in unique_products]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        print(f"\n✓ Generated {len(results)} descriptions in {elapsed:.1f}s")
        
        # Save to cache
        cache_data = [{"name": n, "category": c, "description": d} for n, c, d in results]
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Cached to: {CACHE_FILE}\n")
    
    # Step 3: Batch update PostgreSQL
    print("=" * 60)
    print("PHASE 3: Updating PostgreSQL (all 104,000 rows)")
    print("=" * 60)
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            updated_total = 0
            for name, category, description in results:
                cur.execute("""
                    UPDATE products 
                    SET description = %s 
                    WHERE reference = %s
                """, (description, name))
                count = cur.rowcount
                updated_total += count
            
            conn.commit()
            print(f"\n✓ Updated {updated_total} rows in PostgreSQL.")
    
    # Step 4: Verify
    print("\n" + "=" * 60)
    print("PHASE 4: Verification (Random Sample)")  
    print("=" * 60)
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.reference, c.name, p.description 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                ORDER BY RANDOM() 
                LIMIT 3
            """)
            for row in cur.fetchall():
                print(f"\n  [{row[1]}] {row[0]}:")
                print(f"  {row[2][:200]}...")
    
    print("\n" + "=" * 60)
    print("ENRICHMENT COMPLETE!")
    print("Next step: Run 'make graphrag-neo4j-clean' then 'make graphrag-etl'")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
