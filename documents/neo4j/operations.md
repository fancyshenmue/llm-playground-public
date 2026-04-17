# Neo4j Operations & Cypher Cheat Sheet

This document serves as the operational guide and exhaustive Cypher querying reference for the Neo4j Knowledge Graph deployed in the Enterprise GraphRAG infrastructure.

---

## 1. Connection & Platform Info

### Accessing the Database

- **Web Browser (Browser Interface)**: `http://localhost:7474`
- **Bolt Connection (Application / Langchain)**: `bolt://localhost:7687`
- **Default Credentials**:
  - Username: `neo4j`
  - Password: `password`

### Connecting via Command Line (Cypher-Shell)

If you prefer running operations directly from a terminal without the Web UI:

```bash
docker exec -it <neo4j_container_name> cypher-shell -u neo4j -p password
```

---

## 2. Information & Schema Exploration

Before running deep queries, it is essential to understand what is currently residing inside the Neo4j instance.

### View the Database Schema

This command visualizes how different Node Labels (e.g., `Product`, `Customer`) connect to each other.

```cypher
CALL db.schema.visualization();
```

### Get Total Counts

Count all nodes and relationships instantly to measure data volume.

```cypher
// Count total nodes
MATCH (n) RETURN count(n) AS TotalNodes;

// Count total relationships (edges)
MATCH ()-[r]->() RETURN count(r) AS TotalRelationships;
```

### Inspect Indexes & Constraints

Constraints are crucial to prevent duplicates (`O(N^2)` full scan locks).

```cypher
// List all active constraints (e.g., Unique IDs)
SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties;

// List all active indexes (including Vector & Keyword indexes)
SHOW INDEXES YIELD name, type, state, labelsOrTypes, properties;
```

---

## 3. Creating Nodes & Relationships (Data Ingestion)

### Create vs Merge

- **`CREATE`**: Always forces the creation of a new node/edge. (Can cause duplicates).
- **`MERGE`**: Acts as an "UPSERT" -> It finds the pattern if it exists; if not, it creates it.

### Create a Node

```cypher
// Creating a single node
CREATE (p:Product {id: "1001", title: "Camping Tent", price: 150.0});
```

### Mutate or UPSERT (MERGE)

```cypher
// Find a product by ID, update its properties if it exists, or create it if missing
MERGE (c:Customer {id: "c-123"})
ON CREATE SET c.name = "John Doe", c.created_at = timestamp()
ON MATCH SET c.last_seen = timestamp();
```

### Creating Relationships (Edges)

You must match the source and target nodes first, then connect them using the `(node)-[:RELATIONSHIP]->(node)` arrow syntax.

```cypher
MATCH (p:Product {id: "1001"})
MATCH (c:Category {id: "Outdoor Gear"})
// Create an edge from Product -> Category
MERGE (p)-[:BELONGS_TO]->(c);
```

---

## 4. Querying & Reading (MATCH Operations)

`MATCH` is the equivalent of SQL's `SELECT`.

### Basic Retrieval

```cypher
// Find top 10 Products and return them
MATCH (p:Product)
RETURN p.id, p.title, p.price
LIMIT 10;
```

### Filtering with WHERE

```cypher
// Find products with a specific feature
MATCH (p:Product)-[:HAS_FEATURE]->(f:Feature)
WHERE f.id = "Waterproof" AND p.price < 200
RETURN p.title;
```

### Multi-Hop Queries (The Power of Graph)

_Example: Find Customers who bought products that share the same 'Benefit' as a specific tent._

```cypher
MATCH (c:Customer)-[:WROTE]->(r:Review)-[:ABOUT]->(p1:Product {id: "tent-01"})
MATCH (p1)-[:PROVIDES_BENEFIT]->(b:Benefit)<-[:PROVIDES_BENEFIT]-(p2:Product)
WHERE p1.id <> p2.id
RETURN DISTINCT c.id AS User, p2.title AS RecommendedProduct
ORDER BY p2.price DESC
LIMIT 5;
```

### Aggregating & Counting

_Example: Find which Brands have the most products._

```cypher
MATCH (b:Brand)<-[:PRODUCED_BY]-(p:Product)
RETURN b.id AS BrandName, count(p) AS ProductCount
ORDER BY ProductCount DESC;
```

---

## 5. Updating & Modifying Data (UPDATE Operations)

### Updating Properties (SET)

```cypher
MATCH (p:Product {id: "1001"})
SET p.price = 129.99, p.in_stock = true
RETURN p;
```

### Adding New Labels to Existing Nodes

A node can have multiple labels (e.g., a `Product` can also be marked as `Bestseller`).

```cypher
MATCH (p:Product)
WHERE p.rating > 4.5
SET p:Bestseller
RETURN p.title, labels(p);
```

### Modifying Relationship Properties

Edges can hold data too!

```cypher
MATCH (c:Customer {id: "123"})-[r:PLACED]->(o:Order)
SET r.purchase_date = "2024-04-12"
RETURN type(r), r.purchase_date;
```

---

## 6. Deleting & Scrubbing (DELETE Operations)

> [!CAUTION]
> Be extremely careful with DETACH DELETE without constraints, as it can wipe massive sections of your database.

### Deleting Properties (REMOVE)

```cypher
MATCH (p:Product {id: "1001"})
REMOVE p.in_stock  // Completely deletes the property key from the node
RETURN p;
```

### Deleting a specific Label

```cypher
MATCH (p:Bestseller)
WHERE p.rating < 4.0
REMOVE p:Bestseller  // Strips the nested label but keeps the node
RETURN labels(p);
```

### Deleting a Relationship (Edge)

```cypher
// Remove the BELONGS_TO link between a specific product and category
MATCH (p:Product {id: "1001"})-[r:BELONGS_TO]->(c:Category)
DELETE r;
```

### Deleting a Node entirely

_Note: A node cannot be deleted if it still has edges connected to it. You must use `DETACH DELETE`._

```cypher
// Find exactly this product
MATCH (p:Product {id: "error_node"})
// DETACH destroys all inbound/outbound arrows, then destroys the node
DETACH DELETE p;
```

### Wiping the entire Database (Full Reset)

```cypher
MATCH (n)
DETACH DELETE n;
```

---

## 7. Advanced: Array Manipulation & Vector Interactions

### Handling Arrays in Cypher

When interacting with AI models, you often inject context into Arrays.

```cypher
// Finding nodes based on Array existence using IN
MATCH (p:Product)
WHERE 'Carbon Fiber' IN p.materials
RETURN p.title;

// Reducer for strings (GraphRAG safety)
// Converts an array of review dictionaries into a single safe string
MATCH (p:Product)<-[:ABOUT]-(r:Review)
WITH p, collect({rating: r.rating, comment: r.comment}) AS reviews_array
RETURN reduce(s = '', item in reviews_array | s + '[' + item.rating + ']: ' + item.comment + ' | ') AS ConsolidatedReviews
```

---

## 8. Backup & Restore

> [!IMPORTANT]
> The Neo4j instance in this project runs inside Docker with **named volumes**. All backup strategies below are tailored to this setup:
>
> - **Container**: `graphrag-neo4j`
> - **Data Volume**: `neo4j-data` → `/data` inside the container
> - **Logs Volume**: `neo4j-logs` → `/logs` inside the container
> - **APOC Plugin**: Enabled (export/import enabled via env vars)

### 8.1 Method Comparison

| Method               | Speed  | Portable              | Includes Indexes    | Requires Downtime | Best For                     |
| -------------------- | ------ | --------------------- | ------------------- | ----------------- | ---------------------------- |
| APOC Export (JSON)   | Medium | ✅ Cross-version      | ❌ Must recreate    | No                | Selective / partial backup   |
| APOC Export (Cypher) | Slow   | ✅ Universal text     | ❌ Must recreate    | No                | Migration between versions   |
| Docker Volume Tar    | Fast   | ❌ Same version only  | ✅ Full binary copy | **Yes**           | Disaster recovery snapshot   |
| `neo4j-admin dump`   | Fast   | ⚠️ Same major version | ✅ Full binary dump | **Yes**           | Production-grade full backup |

---

### 8.2 APOC Export (Online — No Downtime)

APOC is already enabled in the Docker Compose config (`NEO4J_PLUGINS=["apoc"]`). These methods work while the database is running.

#### 8.2.1 Export entire graph as JSON

```bash
# Export all nodes and relationships to a JSON file inside the container
docker exec graphrag-neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.export.json.all('/var/lib/neo4j/import/full_backup.json', {})"
```

```bash
# Copy the export file from container to host
docker cp graphrag-neo4j:/var/lib/neo4j/import/full_backup.json ./backups/
```

**Docker Compose equivalent:**

```bash
COMPOSE_FILE=deployments/docker-compose/graphrag-ecommerce/docker-compose.yml

docker compose -f $COMPOSE_FILE exec neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.export.json.all('/var/lib/neo4j/import/full_backup.json', {})"

docker compose -f $COMPOSE_FILE cp neo4j:/var/lib/neo4j/import/full_backup.json ./backups/
```

#### 8.2.2 Export entire graph as Cypher statements

This produces a `.cypher` file containing `CREATE` statements — the most portable format.

```bash
docker exec graphrag-neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.export.cypher.all('/var/lib/neo4j/import/full_backup.cypher', {format: 'plain'})"
```

```bash
docker cp graphrag-neo4j:/var/lib/neo4j/import/full_backup.cypher ./backups/
```

**Docker Compose equivalent:**

```bash
docker compose -f $COMPOSE_FILE exec neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.export.cypher.all('/var/lib/neo4j/import/full_backup.cypher', {format: 'plain'})"

docker compose -f $COMPOSE_FILE cp neo4j:/var/lib/neo4j/import/full_backup.cypher ./backups/
```

#### 8.2.3 Selective export (specific labels only)

```bash
# Export only Product and Category nodes with their connecting edges
docker exec graphrag-neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.export.json.query(
    'MATCH (p:Product)-[r]->(t) RETURN p, r, t',
    '/var/lib/neo4j/import/products_backup.json', {}
  )"
```

**Docker Compose equivalent:**

```bash
docker compose -f $COMPOSE_FILE exec neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.export.json.query(
    'MATCH (p:Product)-[r]->(t) RETURN p, r, t',
    '/var/lib/neo4j/import/products_backup.json', {}
  )"
```

#### 8.2.4 Restore from APOC JSON

```bash
# Copy backup file into container import directory
docker cp ./backups/full_backup.json graphrag-neo4j:/var/lib/neo4j/import/

# Import (will MERGE, not duplicate if constraints exist)
docker exec graphrag-neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.import.json('full_backup.json')"
```

**Docker Compose equivalent:**

```bash
docker compose -f $COMPOSE_FILE cp ./backups/full_backup.json neo4j:/var/lib/neo4j/import/

docker compose -f $COMPOSE_FILE exec neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.import.json('full_backup.json')"
```

#### 8.2.5 Restore from APOC Cypher

```bash
docker cp ./backups/full_backup.cypher graphrag-neo4j:/var/lib/neo4j/import/

# Run the Cypher statements
docker exec graphrag-neo4j cypher-shell -u neo4j -p password \
  < ./backups/full_backup.cypher
```

**Docker Compose equivalent:**

```bash
docker compose -f $COMPOSE_FILE cp ./backups/full_backup.cypher neo4j:/var/lib/neo4j/import/

docker compose -f $COMPOSE_FILE exec -T neo4j cypher-shell -u neo4j -p password \
  < ./backups/full_backup.cypher
```

> [!TIP]
> Set the compose file path once per session to avoid repeating it:
> ```bash
> export COMPOSE_FILE=deployments/docker-compose/graphrag-ecommerce/docker-compose.yml
> # Then all subsequent commands simplify to:
> docker compose exec neo4j cypher-shell -u neo4j -p password "CALL apoc.export.json.all(...)"
> ```

---

### 8.3 Docker Volume Backup (Offline — Binary Snapshot)

> [!WARNING]
> This method requires **stopping the Neo4j container** to ensure data consistency. Never tar a running Neo4j data directory — it will produce a corrupt backup.

#### 8.3.1 Full volume backup

```bash
# 1. Stop the container
docker stop graphrag-neo4j

# 2. Create a timestamped tar archive from the named volume
docker run --rm \
  -v graphrag-ecommerce_neo4j-data:/source:ro \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/neo4j-data-$(date +%Y%m%d_%H%M%S).tar.gz -C /source .

# 3. Restart the container
docker start graphrag-neo4j
```

**Docker Compose equivalent:**

```bash
COMPOSE_FILE=deployments/docker-compose/graphrag-ecommerce/docker-compose.yml

# 1. Stop only Neo4j (keeps PostgreSQL running)
docker compose -f $COMPOSE_FILE stop neo4j

# 2. Tar the volume (same command — volumes are Docker-managed)
docker run --rm \
  -v graphrag-ecommerce_neo4j-data:/source:ro \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/neo4j-data-$(date +%Y%m%d_%H%M%S).tar.gz -C /source .

# 3. Restart
docker compose -f $COMPOSE_FILE start neo4j
```

#### 8.3.2 Restore from volume tar

```bash
# 1. Stop the container
docker stop graphrag-neo4j

# 2. Wipe existing volume data and extract backup
docker run --rm \
  -v graphrag-ecommerce_neo4j-data:/target \
  -v $(pwd)/backups:/backup \
  alpine sh -c "rm -rf /target/* && tar xzf /backup/neo4j-data-YYYYMMDD_HHMMSS.tar.gz -C /target"

# 3. Restart
docker start graphrag-neo4j
```

**Docker Compose equivalent:**

```bash
docker compose -f $COMPOSE_FILE stop neo4j

docker run --rm \
  -v graphrag-ecommerce_neo4j-data:/target \
  -v $(pwd)/backups:/backup \
  alpine sh -c "rm -rf /target/* && tar xzf /backup/neo4j-data-YYYYMMDD_HHMMSS.tar.gz -C /target"

docker compose -f $COMPOSE_FILE start neo4j
```

> [!CAUTION]
> ⚠️ **CRITICAL WARNING**: The restore command above executes `rm -rf /target/*` which **permanently destroys all current Neo4j data** in the volume. Double-confirm the backup file exists and is valid before executing.

---

### 8.4 neo4j-admin dump/load (Official Tool)

The `neo4j-admin` utility produces a single `.dump` file — the officially supported backup format.

#### 8.4.1 Create a dump

```bash
# 1. Stop the database (neo4j-admin requires exclusive access)
docker stop graphrag-neo4j

# 2. Run neo4j-admin dump inside the container
docker run --rm \
  -v graphrag-ecommerce_neo4j-data:/data \
  -v $(pwd)/backups:/backups \
  neo4j:latest \
  neo4j-admin database dump neo4j --to-path=/backups

# 3. Restart
docker start graphrag-neo4j
```

**Docker Compose equivalent:**

```bash
docker compose -f $COMPOSE_FILE stop neo4j

docker run --rm \
  -v graphrag-ecommerce_neo4j-data:/data \
  -v $(pwd)/backups:/backups \
  neo4j:latest \
  neo4j-admin database dump neo4j --to-path=/backups

docker compose -f $COMPOSE_FILE start neo4j
```

This produces `backups/neo4j.dump`.

#### 8.4.2 Restore from dump

```bash
# 1. Stop the container
docker stop graphrag-neo4j

# 2. Load the dump (overwrites existing data)
docker run --rm \
  -v graphrag-ecommerce_neo4j-data:/data \
  -v $(pwd)/backups:/backups \
  neo4j:latest \
  neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true

# 3. Restart
docker start graphrag-neo4j
```

**Docker Compose equivalent:**

```bash
docker compose -f $COMPOSE_FILE stop neo4j

docker run --rm \
  -v graphrag-ecommerce_neo4j-data:/data \
  -v $(pwd)/backups:/backups \
  neo4j:latest \
  neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true

docker compose -f $COMPOSE_FILE start neo4j
```

---

### 8.5 Quick One-Liner Backup (Recommended for Daily Use)

For this project, the fastest daily backup combines APOC (no downtime) with a timestamp:

```bash
# One-liner: APOC JSON export with timestamp
mkdir -p backups && \
docker exec graphrag-neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.export.json.all('/var/lib/neo4j/import/backup_$(date +%Y%m%d).json', {})" && \
docker cp graphrag-neo4j:/var/lib/neo4j/import/backup_$(date +%Y%m%d).json ./backups/ && \
echo "✅ Backup saved to ./backups/backup_$(date +%Y%m%d).json"
```

**Docker Compose equivalent:**

```bash
export COMPOSE_FILE=deployments/docker-compose/graphrag-ecommerce/docker-compose.yml

mkdir -p backups && \
docker compose exec neo4j cypher-shell -u neo4j -p password \
  "CALL apoc.export.json.all('/var/lib/neo4j/import/backup_$(date +%Y%m%d).json', {})" && \
docker compose cp neo4j:/var/lib/neo4j/import/backup_$(date +%Y%m%d).json ./backups/ && \
echo "✅ Backup saved to ./backups/backup_$(date +%Y%m%d).json"
```

---

### 8.6 Post-Restore Verification

After any restore, run these queries to confirm data integrity:

```cypher
// 1. Verify node counts by label
MATCH (n) RETURN labels(n)[0] AS Label, count(n) AS Count ORDER BY Count DESC;

// 2. Verify relationship counts by type
MATCH ()-[r]->() RETURN type(r) AS RelType, count(r) AS Count ORDER BY Count DESC;

// 3. Verify constraints still exist
SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties;

// 4. Verify vector index status
SHOW INDEXES YIELD name, type, state WHERE type = 'VECTOR' OR type = 'FULLTEXT';
```

> [!NOTE]
> After restoring from APOC or Cypher exports, you **must** recreate constraints and vector indexes manually since they are not included in the export. Re-run the ETL's constraint creation or use:
>
> ```cypher
> CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
> CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE;
> CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
> CREATE CONSTRAINT review_id IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE;
> ```
>
> Then regenerate the vector index by running `make graphrag-etl` (it will skip already-extracted products and jump to Part C).
