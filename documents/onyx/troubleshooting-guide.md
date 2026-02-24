# Onyx RAG Troubleshooting Guide

## Overview
This guide documents common issues encountered when integrating Onyx (formerly Danswer) as a RAG provider and their solutions.

## Issue 1: Authentication Failures (403 Access Denied)

### Symptoms
- API calls return `403 Forbidden` or `Access denied` errors
- Project files upload successfully but are not accessible via RAG queries
- `curl` tests with Bearer token fail

### Root Cause
Onyx implements a strict **identity separation** model:
- When you create an API Key, Onyx generates a separate "API User" identity
- This API User has a different UUID than your admin account
- Projects and files created by your admin account are NOT automatically accessible to the API User

### Diagnosis Steps

1. **Identify the API User UUID**:
```bash
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c "SELECT user_id, owner_id FROM api_key;"
```

2. **Check project ownership**:
```bash
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c "SELECT id, name, user_id FROM user_project;"
```

3. **Check file ownership**:
```bash
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c "SELECT id, name, user_id FROM user_file WHERE id IN (SELECT user_file_id FROM project__user_file WHERE project_id = 1);"
```

### Solution

**Option A: Align API Key to Admin User** (Recommended)
```sql
-- Update API key to use admin user identity
UPDATE api_key SET user_id = '79a33dce-0c6b-44cf-a420-a3659b94528c' WHERE id = 1;

-- Update project ownership
UPDATE user_project SET user_id = '79a33dce-0c6b-44cf-a420-a3659b94528c' WHERE id = 1;

-- Update file ownership
UPDATE user_file SET user_id = '79a33dce-0c6b-44cf-a420-a3659b94528c'
FROM project__user_file
WHERE user_file.id = project__user_file.user_file_id
AND project__user_file.project_id = 1;
```

**Option B: Transfer Ownership to API User**
```sql
-- Get API user UUID
API_USER=$(docker exec onyx-relational_db-1 psql -U postgres -d postgres -t -c "SELECT user_id FROM api_key LIMIT 1;")

-- Transfer project to API user
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c "UPDATE user_project SET user_id = '$API_USER' WHERE id = 1;"

-- Transfer files to API user
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c "UPDATE user_file SET user_id = '$API_USER' FROM project__user_file WHERE user_file.id = project__user_file.user_file_id AND project__user_file.project_id = 1;"
```

### Prevention
- Always create API keys while logged in as the same user who will own the projects
- Document the user_id associations for your setup
- Consider using Personas instead of Projects for public/shared RAG contexts

---

## Issue 2: Empty RAG Context Retrieval

### Symptoms
- API returns successful 200 response
- `top_documents` array is empty or contains minimal data
- Generated strategies show hallucinations despite RAG being enabled

### Root Cause
The Onyx API response schema uses `blurb` instead of `content` for document snippets.

### Diagnosis
```bash
ONYX_KEY="your-api-key"
curl -s -X POST "http://localhost:3000/api/chat/send-chat-message" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test query",
    "stream": false,
    "chat_session_info": {"project_id": 1}
  }' | jq '.top_documents[0] | keys'
```

Expected output includes: `blurb`, `document_id`, `semantic_identifier`, `score`, etc.

### Solution
Update your Go struct to map the correct field:
```go
var resp struct {
    Message      string `json:"message"`
    TopDocuments []struct {
        Content string `json:"blurb"`  // NOT "content"
    } `json:"top_documents"`
}
```

---

## Issue 3: "Message ID is required" Error

### Symptoms
- Error: `Message ID is required for continuation`
- Occurs when using `project_id` without proper context

### Root Cause
When using Projects, Onyx expects a conversation thread context.

### Solution
For one-shot RAG queries, ensure you're using the correct endpoint and payload:
```json
{
  "message": "Your query",
  "stream": false,
  "chat_session_info": {
    "project_id": 1
  }
}
```

Do NOT include `parent_message_id` for new conversations.

---

## Issue 4: Document Not Found in Search

### Symptoms
- Files show as "COMPLETED" status
- Files are linked to project
- But RAG queries return no results from those files

### Root Cause
1. **Indexing delay**: Vespa may still be processing the documents
2. **Search permissions**: Document ACL may not include the API user

### Diagnosis
1. Check file status:
```bash
curl -s -X GET "http://localhost:3000/api/user/projects/files/1" \
  -H "Authorization: Bearer $ONYX_KEY" | jq '.[] | {name, status, chunk_count}'
```

2. Wait for `chunk_count` to be populated (indicates indexing complete)

3. Check Vespa logs:
```bash
docker logs onyx-vespa_0-1 --tail 50
```

### Solution
- Allow 30-60 seconds for indexing after upload
- Verify `status` is "COMPLETED" and `chunk_count` > 0
- Check for Vespa errors in container logs

---

## General Debugging Tips

### 1. Check OpenAPI Schema
```bash
curl -s http://localhost:3000/api/openapi.json | jq '.paths | keys'
```

### 2. Monitor API Server Logs
```bash
docker logs onyx-api_server-1 --tail 100 -f
```

### 3. Verify Database State
```bash
# List all projects
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c "SELECT * FROM user_project;"

# List project files
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c "SELECT * FROM project__user_file WHERE project_id = 1;"
```

### 4. Test API Directly
```bash
ONYX_KEY=$(grep -A 2 "onyx:" cmd/go/llm-utils/config.yaml | grep api_key | cut -d: -f2- | xargs | tr -d '"')

curl -s -X POST "http://localhost:3000/api/chat/send-chat-message" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test",
    "stream": false,
    "chat_session_info": {"project_id": 1}
  }' | jq '.'
```

---

## Best Practices

1. **Use Admin User for API Keys**: Create API keys while logged in as the project owner
2. **Verify Indexing**: Always check `chunk_count` after upload before querying
3. **Handle Field Mapping**: Always verify API response schema in your client code
4. **Monitor Resource Usage**: Vespa indexing can be resource-intensive
5. **Use Personas for Public Data**: Projects are best for user-specific contexts
