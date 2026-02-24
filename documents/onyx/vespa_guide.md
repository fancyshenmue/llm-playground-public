# Connecting to Vespa in Onyx

Onyx uses **Vespa** as its primary vector and keyword search engine. This guide explains how to connect to Vespa, inspect its data, and understand how it handles dense and sparse vectors.

## 1. Exposing Vespa Ports

By default, Vespa's ports are not exposed to the host machine. To connect to Vespa from your browser or API tools, you must modify `deployment/docker_compose/docker-compose.yml`.

Find the `index` (Vespa) service and ensure the `ports` section is uncommented:

```yaml
  index:
    image: vespaengine/vespa:8.609.39
    ports:
      - "19071:19071" # Config Server
      - "8081:8081"   # Search / Document API
```

After modifying the file, restart your services:
```bash
docker compose up -d
```

---

## 2. Health and Configuration Checks

Once ports are exposed, you can verify Vespa's status via these URLs:

*   **Config Server Health:** [http://localhost:19071/state/v1/health](http://localhost:19071/state/v1/health)
*   **Search Node Health:** [http://localhost:8081/state/v1/health](http://localhost:8081/state/v1/health)

---

## 3. Querying the Vector Database

Vespa does not have a built-in graphical dashboard like Qdrant. Interaction is primarily through the **Vespa Query API**.

### Identifying the Schema Name
Onyx dynamically generates the schema name based on the embedding model being used. To find your actual schema name, you can check for errors in a generic query or use the config server.

Common schema names look like:
*   `danswer_chunk` (Default)
*   `danswer_chunk_nomic_ai_nomic_embed_text_v1` (If using Nomic)

### Running a YQL Query
You can run an SQL-like query (YQL) directly in your browser:

**Query All Documents:**
`http://localhost:8081/search/?yql=select * from danswer_chunk_nomic_ai_nomic_embed_text_v1 where true`

**Filter by Source Type (e.g., only user files):**
`http://localhost:8081/search/?yql=select * from danswer_chunk_nomic_ai_nomic_embed_text_v1 where source_type contains "user_file"`

**Search for specific content (Keyword search):**
`http://localhost:8081/search/?yql=select * from danswer_chunk_nomic_ai_nomic_embed_text_v1 where content contains "Pine Script"`

**Sort by boost (Importance) and limit to 5 results:**
`http://localhost:8081/search/?yql=select * from danswer_chunk_nomic_ai_nomic_embed_text_v1 where true order by boost desc limit 5`

**Filter by Document ID:**
`http://localhost:8081/search/?yql=select * from danswer_chunk_nomic_ai_nomic_embed_text_v1 where document_id contains "fd5e0416-3953-41d4-8d60-8a42978f9000"`

**Check specific Chunk:**
`http://localhost:8081/search/?yql=select * from danswer_chunk_nomic_ai_nomic_embed_text_v1 where chunk_id == 0`

---

## 4. Understanding the Data Structure

Vespa handles both "dense" (vector) and "sparse" (keyword) search. Unlike Qdrant, which separates them into points, Vespa stores them in a single document schema:

*   **Dense Vectors:** Stored in the `embeddings` and `title_embedding` fields as `tensor` types.
*   **Sparse/Keyword Index:** Handled by the `title` and `content` fields with `bm25` enabled.

### Example JSON Response
When you query the API, you will see a `fields` object containing:
- `document_id`: The unique ID.
- `content`: The raw text content.
- `embeddings`: The numerical vector values (tensors).
- `metadata`: JSON string containing document attributes.

---

## 5. Recommended Tools

*   **Vespa CLI:** For advanced management and querying.
*   **Postman/Insomnia:** Better for visualizing large JSON responses from the `/search/` endpoint.
## 6. Using curl CLI

For users who prefer the command line, you can use `curl` to query Vespa.

### GET Request (Simple)
Note: You must URL-encode the space character as `%20`.

```bash
curl "http://localhost:8081/search/?yql=select%20*%20from%20danswer_chunk_nomic_ai_nomic_embed_text_v1%20where%20true"
```

### POST Request (Recommended for complex queries)
Using POST allows you to send the YQL query in a JSON body, avoiding URL encoding issues.

```bash
curl -X POST -H "Content-Type: application/json" \
     --data '{"yql": "select * from danswer_chunk_nomic_ai_nomic_embed_text_v1 where true"}' \
     "http://localhost:8081/search/"
```

### Pretty Print JSON output
Pipe the output to `jq` for better readability:

```bash
curl -s "http://localhost:8081/search/?yql=select%20*%20from%20danswer_chunk_nomic_ai_nomic_embed_text_v1%20where%20true" | jq
```
