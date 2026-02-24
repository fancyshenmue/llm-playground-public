# Onyx RAG Quick Start Guide

## Prerequisites
- Onyx instance running (via Docker Compose)
- PostgreSQL and Vespa accessible
- Admin account configured

---

## Step 1: Create API Key

### Via Web UI
1. Log in to Onyx at `http://localhost:3000`
2. Navigate to Settings → API Keys
3. Click "Generate New API Key"
4. Copy the key immediately (it won't be shown again)
5. Name it descriptively (e.g., "llm-utils-key")

### Via CLI (Alternative)
```bash
# Access API server container
docker exec -it onyx-api_server-1 bash

# Generate key (requires admin session)
# Note: Easier to use web UI
```

---

## Step 2: Create Project

### Via Web UI
1. Navigate to Projects
2. Click "New Project"
3. Name it (e.g., "pinescript-v6")
4. Add description (optional)

### Verify Creation
```bash
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c \
  "SELECT id, name FROM user_project;"
```

---

## Step 3: Upload Documents

### Method A: Web UI (Recommended for Initial Setup)
1. Open your project
2. Click "Add Files"
3. Select markdown files
4. Wait for upload confirmation
5. Verify files show "COMPLETED" status

### Method B: API Upload
```bash
ONYX_KEY="your-api-key-here"
PROJECT_ID=1

# Upload file
curl -X POST "http://localhost:3000/api/user/projects/file/upload" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -F "files=@documents/quant/pinescript_v6_pitfalls.md" \
  -F "user_project_id=$PROJECT_ID"
```

**Response** will include `file_id` - save this!

### Link File to Project
```bash
FILE_ID="uuid-from-upload-response"

curl -X POST "http://localhost:3000/api/user/projects/$PROJECT_ID/files/$FILE_ID" \
  -H "Authorization: Bearer $ONYX_KEY"
```

---

## Step 4: Verify Indexing

### Check File Status
```bash
curl -X GET "http://localhost:3000/api/user/projects/files/$PROJECT_ID" \
  -H "Authorization: Bearer $ONYX_KEY" | jq '.[] | {name, status, chunk_count}'
```

**Wait for**:
- `status`: "COMPLETED"
- `chunk_count`: Greater than 0

**Typical indexing time**: 30-60 seconds per file

---

## Step 5: Test RAG Query

### Basic Test
```bash
curl -X POST "http://localhost:3000/api/chat/send-chat-message" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the rules for Pine Script v6 trailing stops?",
    "stream": false,
    "chat_session_info": {
      "project_id": 1
    }
  }' | jq '.message'
```

**Expected**: Relevant answer citing your documents

### Verify Document Retrieval
```bash
curl -X POST "http://localhost:3000/api/chat/send-chat-message" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test",
    "stream": false,
    "chat_session_info": {
      "project_id": 1
    }
  }' | jq '.top_documents[] | {semantic_identifier, score}'
```

**Expected**: List of your uploaded files with relevance scores

---

## Step 6: Configure Your Application

### Config File Setup
```yaml
# config.yaml
onyx:
  base_url: "http://localhost:3000"
  api_key: "your-api-key-here"
  persona_id: 0
project_id: 1
```

### Go Client Setup
```go
package main

import (
    "fmt"
    "llm-playground/internal/go/api"
    "llm-playground/cmd/go/llm-utils/config"
)

func main() {
    // Initialize config
    config.InitConfig()

    // Create client
    client := api.NewOnyxClient(
        config.AppConfig.Onyx.BaseURL,
        config.AppConfig.Onyx.APIKey,
    )

    // Query RAG
    response, err := client.Query(
        config.AppConfig.Onyx.PersonaID,
        config.AppConfig.Onyx.ProjectID,
        "Your question here",
    )

    if err != nil {
        panic(err)
    }

    fmt.Println("RAG Context:", response)
}
```

---

## Common First-Time Issues

### Issue: "Access Denied" on Query

**Diagnosis**:
```bash
# Check API key ownership
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c \
  "SELECT user_id, owner_id FROM api_key WHERE id = 1;"

# Check project ownership
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c \
  "SELECT user_id FROM user_project WHERE id = 1;"
```

**Fix** (if UUIDs don't match):
```bash
ADMIN_UUID="your-admin-uuid-here"

docker exec onyx-relational_db-1 psql -U postgres -d postgres -c \
  "UPDATE api_key SET user_id = '$ADMIN_UUID' WHERE id = 1;"

docker exec onyx-relational_db-1 psql -U postgres -d postgres -c \
  "UPDATE user_project SET user_id = '$ADMIN_UUID' WHERE id = 1;"
```

### Issue: Empty `top_documents`

**Possible Causes**:
1. Files not finished indexing (`chunk_count` is NULL)
2. Query doesn't match document content
3. Project ID incorrect

**Debug**:
```bash
# Verify indexing
curl -X GET "http://localhost:3000/api/user/projects/files/$PROJECT_ID" \
  -H "Authorization: Bearer $ONYX_KEY" | jq '.[] | select(.chunk_count == null)'

# Test with broad query
curl -X POST "http://localhost:3000/api/chat/send-chat-message" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Give me any information from the documents",
    "stream": false,
    "chat_session_info": {"project_id": 1}
  }' | jq '.top_documents | length'
```

### Issue: "Message ID Required"

**Cause**: Using chat continuation params incorrectly

**Fix**: For one-shot queries, use:
```json
{
  "message": "Your query",
  "stream": false,
  "chat_session_info": {
    "project_id": 1
  }
}
```

Do NOT include `parent_message_id` or existing `chat_session_id` for new conversations.

---

## Next Steps

1. **Read the Troubleshooting Guide**: [`troubleshooting-guide.md`](troubleshooting-guide.md)
2. **Review API Reference**: [`api-reference.md`](api-reference.md)
3. **Understand Database Schema**: [`database-schema.md`](database-schema.md)
4. **Optimize Your Prompts**: See your application's RAG documentation

---

## Production Checklist

- [ ] API keys stored securely (not in git)
- [ ] Error handling for failed queries
- [ ] Timeout configuration (60s recommended)
- [ ] Monitoring for `chunk_count` on new uploads
- [ ] Backup strategy for PostgreSQL database
- [ ] Resource limits configured for Vespa
- [ ] Rate limiting implemented in your client
- [ ] Logging for RAG query performance

---

## Useful Commands Reference

```bash
# Health check
curl -s http://localhost:3000/health

# List all projects
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c \
  "SELECT * FROM user_project;"

# Monitor API logs
docker logs onyx-api_server-1 --tail 100 -f

# Check Vespa status
curl -s http://localhost:8080/state/v1/health

# Database shell
docker exec -it onyx-relational_db-1 psql -U postgres -d postgres
```
