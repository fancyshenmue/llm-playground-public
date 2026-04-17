# Langfuse Operations Guide

## 1. Local Deployment (Docker Compose)
Langfuse is self-hosted via Docker Compose. The stack runs a web server, ingestion worker, PostgreSQL, ClickHouse, Redis, and MinIO locally.

To spin up the observability stack:
```bash
make langfuse-up
```

To tear it down cleanly:
```bash
make langfuse-down
```

> **Note:** The telemetry PostgreSQL instance is specifically mapped to port `5433` (instead of 5432) to prevent collisions with the primary LangGraph/pgvector database running parallel on the same host.

## 2. Generating API Keys
Once the stack is healthy, browse to the Web UI at:
- **URL**: `http://localhost:3000`
- **Initial Setup**: Create any local admin account credentials (offline, not submitted externally).
- Go to `Settings -> API Keys` and generate a definitive `Secret Key` and `Public Key`.

## 3. Configuration
Add the newly generated keys to your **backend configuration** file, `cmd/py/llm-utils/config.yaml`, eliminating the need for `.env` files and strictly centralizing configurations:
```yaml
observability:
  backend: "langfuse"
  langfuse:
    secret_key: "sk-lf-......."
    public_key: "pk-lf-......."
    host: "http://localhost:3000"
```

## 4. Validating Traces
Start the Enterprise API server and lab UI. Run a coding query via the React interface.
1. Open the Langfuse Web Console (http://localhost:3000).
2. Navigate to the **Traces** pane.
3. You will immediately see highly structured traces. 
4. The React Client's `thread_id` will be mapped exactly to Langfuse's column `Session ID`. You can filter traces directly clicking on `Sessions`.

---

## 5. Infrastructure Component Operations

### 5.1 PostgreSQL (Application Metadata)

| Property | Value |
|---|---|
| Image | `postgres:15` |
| Host Port | `5433` (mapped from internal `5432`) |
| Volume | `langfuse_db_data` |
| Credentials | `postgres` / `postgres` |
| Database | `postgres` |

**Health Check:**
```bash
docker exec $(docker ps -qf "name=langfuse.*postgres") pg_isready -U postgres
```

**Connect via CLI:**
```bash
psql -h 127.0.0.1 -p 5433 -U postgres -d postgres
```

**Inspect Tables (useful for debugging):**
```sql
-- List all Langfuse tables
\dt

-- Count traces
SELECT COUNT(*) FROM traces;

-- Count sessions
SELECT COUNT(*) FROM trace_sessions;
```

**Backup:**
```bash
pg_dump -h 127.0.0.1 -p 5433 -U postgres postgres > langfuse_pg_backup.sql
```

**Restore:**
```bash
psql -h 127.0.0.1 -p 5433 -U postgres postgres < langfuse_pg_backup.sql
```

---

### 5.2 ClickHouse (Trace Analytics Engine)

| Property | Value |
|---|---|
| Image | `clickhouse/clickhouse-server` |
| HTTP Port | `8123` |
| Native TCP Port | `9000` |
| Volume | `langfuse_clickhouse_data` |
| Credentials | `clickhouse` / `clickhouse` |

**Health Check:**
```bash
curl -s http://127.0.0.1:8123/ping
# Expected: "Ok."
```

**Query via HTTP (useful for quick diagnostics):**
```bash
# Count total trace observations
curl -s "http://127.0.0.1:8123/?user=clickhouse&password=clickhouse" \
  -d "SELECT count() FROM traces"

# List tables in default database
curl -s "http://127.0.0.1:8123/?user=clickhouse&password=clickhouse" \
  -d "SHOW TABLES"

# Check disk usage
curl -s "http://127.0.0.1:8123/?user=clickhouse&password=clickhouse" \
  -d "SELECT formatReadableSize(sum(bytes_on_disk)) FROM system.parts WHERE active"
```

**Connect via CLI (inside container):**
```bash
docker exec -it $(docker ps -qf "name=langfuse.*clickhouse") \
  clickhouse-client --user clickhouse --password clickhouse
```

---

### 5.3 Redis (Job Queue & Cache)

| Property | Value |
|---|---|
| Image | `redis:7` |
| Host Port | `6379` |
| Volume | `langfuse_redis_data` |
| Password | `myredissecret` |

**Health Check:**
```bash
redis-cli -h 127.0.0.1 -p 6379 -a myredissecret ping
# Expected: "PONG"
```

**Monitor Queue Activity (live stream):**
```bash
redis-cli -h 127.0.0.1 -p 6379 -a myredissecret MONITOR
```

**Check Queue Depth (pending ingestion jobs):**
```bash
redis-cli -h 127.0.0.1 -p 6379 -a myredissecret DBSIZE
```

**Flush All Queues (⚠️ DESTRUCTIVE — in-flight traces will be lost):**
```bash
redis-cli -h 127.0.0.1 -p 6379 -a myredissecret FLUSHALL
```

---

### 5.4 MinIO (S3-Compatible Blob Storage)

| Property | Value |
|---|---|
| Image | `minio/minio` |
| API Port | `9090` (mapped from internal `9000`) |
| Console Port | `9091` (mapped from internal `9001`) |
| Volume | `langfuse_minio_data` |
| Credentials | `minio` / `miniosecret` |
| Bucket | `langfuse` (auto-created on startup) |

**Web Console:**
- URL: `http://localhost:9091`
- Login: `minio` / `miniosecret`

**Health Check:**
```bash
curl -s http://127.0.0.1:9090/minio/health/live
# Expected: HTTP 200
```

**List Bucket Contents (via mc CLI):**
```bash
# Configure alias (one-time)
mc alias set langfuse-local http://127.0.0.1:9090 minio miniosecret

# List objects in the langfuse bucket
mc ls langfuse-local/langfuse

# Check bucket disk usage
mc du langfuse-local/langfuse
```

---

## 6. Volume Management

All persistent data is stored in Docker named volumes:

| Volume | Service | Data |
|---|---|---|
| `langfuse_db_data` | PostgreSQL | User accounts, API keys, session/trace indexes |
| `langfuse_clickhouse_data` | ClickHouse | Raw trace spans, token metrics, analytics |
| `langfuse_redis_data` | Redis | Job queue state, session cache |
| `langfuse_minio_data` | MinIO | Oversized trace payloads, blob exports |

**List all volumes:**
```bash
docker volume ls | grep langfuse
```

**Inspect a specific volume:**
```bash
docker volume inspect langfuse_db_data
```

**⚠️ Full Reset (DESTROYS all telemetry data):**
```bash
make langfuse-down
docker volume rm langfuse_db_data langfuse_clickhouse_data langfuse_minio_data langfuse_redis_data
make langfuse-up
```
