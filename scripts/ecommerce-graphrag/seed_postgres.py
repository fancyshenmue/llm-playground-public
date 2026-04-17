import os
import json
import psycopg
from datetime import datetime

# Connection string
# Based on docker-compose map: port 5432, user postgres, password postgres, db ecommerce
CONN_STR = "postgresql://postgres:password@localhost:5432/ecommerce"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

DDL = """
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE categories (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR(255) NOT NULL
);

CREATE TABLE customers (
    id          INTEGER PRIMARY KEY,
    first_name  VARCHAR(255),
    last_name   VARCHAR(255),
    email       VARCHAR(255),
    address     TEXT,
    city        VARCHAR(255),
    zipcode     VARCHAR(20),
    avatar      TEXT,
    birthday    DATE,
    nb_commands INTEGER DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0
);

CREATE TABLE products (
    id          INTEGER PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    reference   VARCHAR(255),
    price       DECIMAL(10,2),
    stock       INTEGER DEFAULT 0,
    width       DECIMAL(6,2),
    height      DECIMAL(6,2),
    description TEXT,
    image       TEXT,
    thumbnail   TEXT
);

CREATE TABLE orders (
    id          INTEGER PRIMARY KEY,
    date        TIMESTAMP,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    total       DECIMAL(12,2),
    status      VARCHAR(50),
    returned    BOOLEAN DEFAULT FALSE
);

CREATE TABLE order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id  INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity    INTEGER
);

CREATE TABLE invoices (
    id          INTEGER PRIMARY KEY,
    date        TIMESTAMP,
    order_id    INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    total       DECIMAL(12,2)
);

CREATE TABLE reviews (
    id          INTEGER PRIMARY KEY,
    date        TIMESTAMP,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    product_id  INTEGER REFERENCES products(id) ON DELETE CASCADE,
    rating      INTEGER,
    comment     TEXT,
    status      VARCHAR(50)
);
"""

def parse_date(date_str):
    if not date_str: return None
    # generator outputs date strings like "2023-11-20T10:15:30.000Z"
    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

def load_data():
    with psycopg.connect(CONN_STR) as conn:
        with conn.cursor() as cur:
            print("1. Creating schemas...")
            cur.execute(DDL)
            conn.commit()

            print("2. Seeding categories...")
            with cur.copy("COPY categories (id, name) FROM STDIN") as copy:
                with open(os.path.join(DATA_DIR, "categories.jsonl"), 'r') as f:
                    for line in f:
                        obj = json.loads(line.strip())
                        copy.write_row((obj['id'], obj['name']))
            
            print("3. Seeding customers...")
            with cur.copy("COPY customers (id, first_name, last_name, email, address, city, zipcode, avatar, birthday, nb_commands, total_spent) FROM STDIN") as copy:
                with open(os.path.join(DATA_DIR, "customers.jsonl"), 'r') as f:
                    for line in f:
                        obj = json.loads(line.strip())
                        copy.write_row((
                            obj['id'], obj.get('first_name'), obj.get('last_name'), obj.get('email'),
                            obj.get('address'), obj.get('city'), obj.get('zipcode'), obj.get('avatar'),
                            parse_date(obj.get('birthday')), obj.get('nb_commands', 0), obj.get('total_spent', 0)
                        ))

            print("4. Seeding products...")
            with cur.copy("COPY products (id, category_id, reference, price, stock, width, height, description, image, thumbnail) FROM STDIN") as copy:
                with open(os.path.join(DATA_DIR, "products.jsonl"), 'r') as f:
                    for line in f:
                        obj = json.loads(line.strip())
                        copy.write_row((
                            obj['id'], obj['category_id'], obj.get('reference'), obj.get('price'),
                            obj.get('stock', 0), obj.get('width'), obj.get('height'),
                            obj.get('description'), obj.get('image'), obj.get('thumbnail')
                        ))

            print("5. Seeding orders...")
            with cur.copy("COPY orders (id, date, customer_id, total, status, returned) FROM STDIN") as copy_orders:
                with open(os.path.join(DATA_DIR, "orders.jsonl"), 'r') as f:
                    for line in f:
                        obj = json.loads(line.strip())
                        copy_orders.write_row((
                            obj['id'], parse_date(obj.get('date')), obj['customer_id'],
                            obj.get('total'), obj.get('status'), obj.get('returned', False)
                        ))

            print("5b. Seeding order_items...")
            with cur.copy("COPY order_items (order_id, product_id, quantity) FROM STDIN") as copy_items:
                with open(os.path.join(DATA_DIR, "orders.jsonl"), 'r') as f:
                    for line in f:
                        obj = json.loads(line.strip())
                        for item in obj.get('basket', []):
                            copy_items.write_row((obj['id'], item['product_id'], item.get('quantity', 1)))

            print("6. Seeding invoices...")
            with cur.copy("COPY invoices (id, date, order_id, customer_id, total) FROM STDIN") as copy:
                with open(os.path.join(DATA_DIR, "invoices.jsonl"), 'r') as f:
                    for line in f:
                        obj = json.loads(line.strip())
                        copy.write_row((
                            obj['id'], parse_date(obj.get('date')), obj['order_id'],
                            obj['customer_id'], obj.get('total')
                        ))

            print("7. Seeding reviews...")
            with cur.copy("COPY reviews (id, date, customer_id, product_id, rating, comment, status) FROM STDIN") as copy:
                with open(os.path.join(DATA_DIR, "reviews.jsonl"), 'r') as f:
                    for line in f:
                        obj = json.loads(line.strip())
                        copy.write_row((
                            obj['id'], parse_date(obj.get('date')), obj['customer_id'],
                            obj['product_id'], obj.get('rating'), obj.get('comment'), obj.get('status')
                        ))

        conn.commit()
        print("All chunks seeded successfully into PostgreSQL!")

if __name__ == "__main__":
    load_data()
