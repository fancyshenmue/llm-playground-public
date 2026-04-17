import click
import os
import random
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Try loading from backend if running from root
load_dotenv("backend/ecommerce-graphrag/.env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

MOCK_DATA = [
    # 登山用品 (Outdoor & Mountain Climbing)
    {
        "name": "Gore-Tex 終極防水夾克",
        "description": "採用三層 Gore-Tex Pro 布料，提供最頂級的防水與透氣性能，適合極端氣候攀登。",
        "price": 14500,
        "brand": "Arc'teryx",
        "category": "機能服飾",
        "scenarios": ["高山縱走", "百岳攀登", "雪地攀登"],
        "features": ["防水", "防風", "透氣", "輕量化"]
    },
    {
        "name": "超輕量碳纖維避震登山杖",
        "description": "三節式快扣設計，單支僅重190g，內建抗震系統保護膝關節。",
        "price": 3200,
        "brand": "Black Diamond",
        "category": "登山裝備",
        "scenarios": ["高山縱走", "百岳攀登", "健行"],
        "features": ["輕量化", "避震", "快速調節"]
    },
    # 健康食品 (Health Supplements & Foods)
    {
        "name": "極限高單位游離型葉黃素",
        "description": "含有專利游離型葉黃素與蝦紅素，保護長時間暴露在強光下的雙眼。",
        "price": 1200,
        "brand": "健康優力",
        "category": "營養補充品",
        "scenarios": ["日常保健", "高山縱走", "雪地攀登"],
        "features": ["抗氧化", "眼睛保護", "高劑量"]
    },
    {
        "name": "速效恢復乳清蛋白-高能量版",
        "description": "添加 BCAA 與麩醯胺酸，快速修復受損肌肉，適合高強度運動後補充。",
        "price": 1800,
        "brand": "ON",
        "category": "營養補充品",
        "scenarios": ["運動恢復", "百岳攀登"],
        "features": ["高蛋白", "快速吸收", "肌肉修復"]
    },
    # 3C 與穿戴裝置 (3C Electronics)
    {
        "name": "Fenix 7X 太陽能 GPS 智慧腕錶",
        "description": "具備強大太陽能充電與內建等高線地圖，健康偵測包含血氧與心率。",
        "price": 31900,
        "brand": "Garmin",
        "category": "智慧穿戴",
        "scenarios": ["高山縱走", "百岳攀登", "日常保健"],
        "features": ["GPS定位", "心率監測", "血氧量測", "太陽能充電", "防水"]
    },
    # 護膚與防護 (Skincare & Cosmetics)
    {
        "name": "極地救援高係數防曬乳 SPF50+ PA++++",
        "description": "海洋友善配方，抗高山紫外線，不脫妝且高度防水防汗。",
        "price": 850,
        "brand": "Anessa",
        "category": "防曬護膚",
        "scenarios": ["百岳攀登", "雪地攀登", "戶外活動"],
        "features": ["防曬", "防水", "海洋友善", "抗紫外線"]
    },
    # 寵物用品 (Pet Supplies)
    {
        "name": "K9 探險家寵物保暖衝鋒衣",
        "description": "專為大型犬設計的戶外保暖衣，外層防風防潑水，內層刷毛保暖。",
        "price": 2400,
        "brand": "Ruffwear",
        "category": "寵物服飾",
        "scenarios": ["百岳攀登", "攜帶寵物", "雪地攀登"],
        "features": ["保暖", "防水", "防風", "反光標誌"]
    },
    {
        "name": "犬用關節強效保健肉塊",
        "description": "富含葡萄糖胺與軟骨素的適口性肉條，幫助戶外活動犬隻保護關節。",
        "price": 1100,
        "brand": "PetCare",
        "category": "寵物保健",
        "scenarios": ["攜帶寵物", "日常保健"],
        "features": ["關節保護", "營養補充", "高適口性"]
    }
]

CATEGORIES = ["機能服飾", "登山裝備", "營養補充品", "智慧穿戴", "防曬護膚", "寵物服飾", "寵物保健", "露營用具", "極限攀岩", "野營裝備"]
BRANDS = ["Arc'teryx", "Black Diamond", "Garmin", "Anessa", "Ruffwear", "Patagonia", "Snow Peak", "Salomon", "Osprey", "Columbia", "Mammut", "The North Face", "Naturehike", "PetCare", "ON", "健康優力"]
SCENARIOS = ["高山縱走", "百岳攀登", "雪地攀登", "健行", "日常保健", "運動恢復", "戶外活動", "攜帶寵物", "露營", "冰河探險", "野跑", "健身訓練"]
FEATURES = ["防水", "防風", "透氣", "輕量化", "避震", "快速調節", "抗氧化", "眼睛保護", "高劑量", "高蛋白", "快速吸收", "肌肉修復", "GPS定位", "心率監測", "血氧量測", "太陽能充電", "防曬", "海洋友善", "抗紫外線", "保暖", "反光標誌", "關節保護", "營養補充", "高適口性", "耐磨", "抗菌", "快乾"]

PREFIXES = ["極致", "終極", "超輕量", "專業", "高效", "無敵", "強化", "戰術", "特仕版", "經典", "旗艦", "進化版", "高能量", "強效"]
NOUNS = ["夾克", "登山杖", "帳篷", "背包", "軟殼衣", "睡袋", "頭燈", "手錶", "營養粉", "防曬乳", "衝鋒衣", "肉塊", "護膝", "跑鞋", "登山鞋", "淨水器", "登山爐", "睡墊", "保溫瓶"]

def generate_mass_data(count: int):
    data = []
    for i in range(count):
        cat = random.choice(CATEGORIES)
        brand = random.choice(BRANDS)
        prefix = random.choice(PREFIXES)
        noun = random.choice(NOUNS)
        # Adding a unique serial identifier suffix to guarantee NO constraint collisions
        name = f"{brand} {prefix}{cat}{noun} S{i:06d}"

        data.append({
            "name": name,
            "description": f"精選來自 {brand} 的 {cat}。此為 {prefix} {noun}，專為提升您的活動體驗而設計。高品質保證，適合專業及日常使用。",
            "price": random.randint(50, 1500) * 10,
            "brand": brand,
            "category": cat,
            "scenarios": random.sample(SCENARIOS, k=random.randint(1, 4)),
            "features": random.sample(FEATURES, k=random.randint(2, 5))
        })
    return data


def create_constraint(tx):
    # Ensure product uniqueness
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Scenario) REQUIRE s.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:Feature) REQUIRE f.name IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE")

    # Adding FULLTEXT indexes to speed up broad searching in GraphCypherQAChain if supported
    # In Neo4j 5.x:
    try:
        tx.run("CREATE FULLTEXT INDEX product_text_idx IF NOT EXISTS FOR (n:Product) ON EACH [n.name, n.description]")
    except Exception as e:
        pass

def insert_product(tx, product):
    query = """
    MERGE (p:Product {name: $name})
    SET p.price = $price, p.description = $description
    MERGE (c:Category {name: $category})
    MERGE (p)-[:BELONGS_TO]->(c)
    MERGE (b:Brand {name: $brand})
    MERGE (p)-[:PRODUCED_BY]->(b)
    """

    tx.run(query,
           name=product["name"],
           price=product["price"],
           description=product["description"],
           category=product["category"],
           brand=product["brand"])

    # Link Scenarios
    for scenario in product.get("scenarios", []):
        tx.run("""
        MATCH (p:Product {name: $name})
        MERGE (s:Scenario {name: $scenario})
        MERGE (p)-[:SUITABLE_FOR]->(s)
        """, name=product["name"], scenario=scenario)

    # Link Features
    for feature in product.get("features", []):
        tx.run("""
        MATCH (p:Product {name: $name})
        MERGE (f:Feature {name: $feature})
        MERGE (p)-[:HAS_FEATURE]->(f)
        """, name=product["name"], feature=feature)

def insert_products_bulk(tx, batch):
    query = """
    UNWIND $batch AS p
    MERGE (prod:Product {name: p.name})
    SET prod.price = p.price, prod.description = p.description

    MERGE (c:Category {name: p.category})
    MERGE (prod)-[:BELONGS_TO]->(c)

    MERGE (b:Brand {name: p.brand})
    MERGE (prod)-[:PRODUCED_BY]->(b)

    WITH prod, p
    UNWIND p.scenarios AS scenario
    MERGE (s:Scenario {name: scenario})
    MERGE (prod)-[:SUITABLE_FOR]->(s)

    WITH prod, p
    UNWIND p.features AS feature
    MERGE (f:Feature {name: feature})
    MERGE (prod)-[:HAS_FEATURE]->(f)
    """
    tx.run(query, batch=batch)

@click.group()
def cli():
    """LLM Utils CLI Tool for GraphRAG E-Commerce"""
    pass

@cli.command()
def seed():
    """Seed the Neo4j database with basic mock ecommerce data (8 items)."""
    click.echo(f"Connecting to Neo4j at {NEO4J_URI}...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        with driver.session() as session:
            # Clear existing data
            click.echo("Clearing existing data...")
            session.run("MATCH (n) DETACH DELETE n")

            # Setup constraints
            click.echo("Creating constraints...")
            session.execute_write(create_constraint)

            # Insert data
            click.echo("Inserting GraphRAG data elements...")
            for i, p in enumerate(MOCK_DATA):
                session.execute_write(insert_product, p)
                click.echo(f"  Inserted: {p['name']}")

        driver.close()
        click.echo("Data seeded successfully!")
    except Exception as e:
        click.secho(f"Error seeding data: {e}", fg="red")

@cli.command()
@click.option('--count', default=100000, help='Number of mock products to generate.')
def seed_large(count):
    """Seed the Neo4j database with MASSIVE block of mock data (default 100k)."""
    click.echo(f"Generating {count} mock product datasets in memory...")
    start_time = time.time()
    mock_batch = generate_mass_data(count)
    click.echo(f"Generated successfully in {time.time()-start_time:.2f} seconds.")

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        with driver.session() as session:
            # Clear existing data
            click.echo("Clearing existing data...")
            session.run("MATCH (n) DETACH DELETE n")

            # Setup constraints
            click.echo("Creating constraints...")
            session.execute_write(create_constraint)

            # Insert data in chunks
            click.echo(f"Inserting {count} nodes in chunks to avoid memory overflow...")
            chunk_size = 1000
            for i in range(0, count, chunk_size):
                batch = mock_batch[i:i+chunk_size]
                try:
                    session.execute_write(insert_products_bulk, batch)
                except Exception as ex:
                    # Sometimes category merge constraints can conflict concurrently in a big batch unwind
                    # But sequential execute_write across separate batches should be fine
                    click.secho(f"Batch {i//chunk_size + 1} partial error: {ex}", fg="yellow")

                if (i // chunk_size + 1) % 10 == 0:
                    click.echo(f"  Inserted chunk {i//chunk_size + 1}/{(count//chunk_size)+1}")

        driver.close()
        click.secho(f"Mass Data seeded successfully in {time.time()-start_time:.2f} seconds!", fg="green")
    except Exception as e:
        click.secho(f"Error seeding mass data: {e}", fg="red")

if __name__ == '__main__':
    cli()
