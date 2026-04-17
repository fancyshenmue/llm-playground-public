import generateData from 'data-generator-retail';
import fs from 'fs';
import path from 'path';

const BATCHES = 800; // ~130 products per batch * 800 = ~104,000 products
const OFFSET = 1000000;
const OUTPUT_DIR = './data';

if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const fds = {
    categories: fs.createWriteStream(path.join(OUTPUT_DIR, 'categories.jsonl')),
    customers: fs.createWriteStream(path.join(OUTPUT_DIR, 'customers.jsonl')),
    products: fs.createWriteStream(path.join(OUTPUT_DIR, 'products.jsonl')),
    orders: fs.createWriteStream(path.join(OUTPUT_DIR, 'orders.jsonl')),
    invoices: fs.createWriteStream(path.join(OUTPUT_DIR, 'invoices.jsonl')),
    reviews: fs.createWriteStream(path.join(OUTPUT_DIR, 'reviews.jsonl')),
};

console.log(`Starting generation of ${BATCHES} batches (Goal: ~104k products)...`);

for (let i = 0; i < BATCHES; i++) {
    const data = generateData({ serializeDate: true });
    const shift = i * OFFSET;

    // Categories
    data.categories.forEach(c => {
        c.id = c.id + shift;
        fds.categories.write(JSON.stringify(c) + '\n');
    });

    // Customers
    data.customers.forEach(c => {
        c.id = c.id + shift;
        fds.customers.write(JSON.stringify(c) + '\n');
    });

    // Products
    data.products.forEach(p => {
        p.id = p.id + shift;
        p.category_id = p.category_id + shift;
        fds.products.write(JSON.stringify(p) + '\n');
    });

    // Orders
    data.orders.forEach(o => {
        o.id = o.id + shift;
        o.customer_id = o.customer_id + shift;
        o.basket.forEach(item => {
            item.product_id = item.product_id + shift;
        });
        fds.orders.write(JSON.stringify(o) + '\n');
    });

    // Invoices
    data.invoices.forEach(inv => {
        inv.id = inv.id + shift;
        inv.order_id = inv.order_id + shift;
        inv.customer_id = inv.customer_id + shift;
        fds.invoices.write(JSON.stringify(inv) + '\n');
    });

    // Reviews
    data.reviews.forEach(r => {
        r.id = r.id + shift;
        r.customer_id = r.customer_id + shift;
        r.product_id = r.product_id + shift;
        fds.reviews.write(JSON.stringify(r) + '\n');
    });

    if ((i + 1) % 50 === 0) {
        console.log(`Generated ${i + 1}/${BATCHES} batches...`);
    }
}

// Close all streams
Object.values(fds).forEach(stream => stream.end());
console.log('Data generation complete!');
