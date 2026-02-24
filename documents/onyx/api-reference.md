# Onyx API Reference Guide

## Base Configuration

### Environment
```yaml
onyx:
  base_url: "http://localhost:3000"
  api_key: "your-api-key-here"
  persona_id: 0  # 0 for default
  project_id: 1  # Your project ID
```

### Authentication
All API requests require Bearer token authentication:
```bash
Authorization: Bearer your-api-key-here
```

---

## Core Endpoints

### 1. Upload Files to Project

**Endpoint**: `POST /api/user/projects/file/upload`

**Purpose**: Upload one or more files to a user's project for RAG indexing

**Request**:
```bash
curl -X POST "http://localhost:3000/api/user/projects/file/upload" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -F "files=@path/to/file.md" \
  -F "user_project_id=1"
```

**Response**:
```json
{
  "user_files": [
    {
      "id": "uuid",
      "name": "file.md",
      "status": "PROCESSING",
      "token_count": 1500,
      "chunk_count": null,
      "file_type": "application/octet-stream"
    }
  ],
  "rejected_files": []
}
```

**Key Fields**:
- `status`: "PROCESSING" → "COMPLETED" → "FAILED"
- `chunk_count`: `null` until indexing complete, then shows number of chunks
- `token_count`: Estimated token count for the file

---

### 2. Link File to Project

**Endpoint**: `POST /api/user/projects/{project_id}/files/{file_id}`

**Purpose**: Associate an uploaded file with a specific project

**Request**:
```bash
curl -X POST "http://localhost:3000/api/user/projects/1/files/{file_uuid}" \
  -H "Authorization: Bearer $ONYX_KEY"
```

**Response**:
```json
{
  "id": "file-uuid",
  "name": "file.md",
  "project_id": null,
  "status": "COMPLETED",
  "chunk_count": 3
}
```

**Notes**:
- `project_id` field may remain `null` in response (this is expected)
- Actual association is tracked in `project__user_file` junction table

---

### 3. List Project Files

**Endpoint**: `GET /api/user/projects/files/{project_id}`

**Purpose**: Retrieve all files associated with a project

**Request**:
```bash
curl -X GET "http://localhost:3000/api/user/projects/files/1" \
  -H "Authorization: Bearer $ONYX_KEY"
```

**Response**:
```json
[
  {
    "id": "uuid",
    "file_id": "file-uuid",
    "name": "document.md",
    "status": "COMPLETED",
    "chunk_count": 5,
    "token_count": 2000
  }
]
```

---

### 4. Remove File from Project

**Endpoint**: `DELETE /api/user/projects/{project_id}/files/{file_id}`

**Purpose**: Unlink a file from a project (does not delete the file)

**Request**:
```bash
curl -X DELETE "http://localhost:3000/api/user/projects/1/files/{file_uuid}" \
  -H "Authorization: Bearer $ONYX_KEY"
```

**Response**: Empty (204 No Content)

---

### 5. RAG Query (Chat)

**Endpoint**: `POST /api/chat/send-chat-message`

**Purpose**: Send a query and retrieve RAG-grounded responses

**Request**:
```bash
curl -X POST "http://localhost:3000/api/chat/send-chat-message" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Your question here",
    "stream": false,
    "chat_session_info": {
      "project_id": 1
    }
  }'
```

**Response Schema**:
```json
{
  "message": "AI generated response",
  "top_documents": [
    {
      "blurb": "Relevant text snippet from doc",
      "document_id": "uuid",
      "semantic_identifier": "filename.md",
      "score": 0.85,
      "chunk_ind": 0,
      "match_highlights": [],
      "is_relevant": true
    }
  ],
  "citation_info": [
    {
      "type": "citation_info",
      "citation_number": 1,
      "document_id": "uuid"
    }
  ],
  "message_id": 42,
  "chat_session_id": "session-uuid",
  "error_msg": null
}
```

**Critical Fields**:
- `top_documents[].blurb`: The actual text content (NOT `content`)
- `top_documents[].score`: Relevance score (0.0 to 1.0)
- `error_msg`: Will contain error details if query failed

**Common Parameters**:
```json
{
  "message": "string",
  "stream": false,                    // true for SSE streaming
  "chat_session_info": {
    "project_id": 1,                  // For project-scoped queries
    "persona_id": 0,                  // For persona-scoped queries
    "chat_session_id": "uuid"         // For continuing conversations
  },
  "parent_message_id": null           // For threaded conversations
}
```

---

## Go Client Implementation

### Basic Client Structure

```go
type OnyxClient struct {
    BaseURL string
    APIKey  string
    HTTP    *http.Client
}

func NewOnyxClient(baseURL, apiKey string) *OnyxClient {
    return &OnyxClient{
        BaseURL: baseURL,
        APIKey:  apiKey,
        HTTP:    &http.Client{Timeout: 60 * time.Second},
    }
}
```

### Query Implementation

```go
func (c *OnyxClient) Query(personaID, projectID int, message string) (string, error) {
    url := fmt.Sprintf("%s/api/chat/send-chat-message", c.BaseURL)

    reqBody := map[string]interface{}{
        "message": message,
        "stream":  false,
    }

    // Build chat_session_info
    sessionInfo := make(map[string]interface{})
    if personaID > 0 {
        sessionInfo["persona_id"] = personaID
    }
    if projectID > 0 {
        sessionInfo["project_id"] = projectID
    }
    if len(sessionInfo) > 0 {
        reqBody["chat_session_info"] = sessionInfo
    }

    payload, _ := json.Marshal(reqBody)

    httpReq, _ := http.NewRequest("POST", url, bytes.NewBuffer(payload))
    httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.APIKey))
    httpReq.Header.Set("Content-Type", "application/json")

    res, err := c.HTTP.Do(httpReq)
    if err != nil {
        return "", err
    }
    defer res.Body.Close()

    if res.StatusCode != http.StatusOK {
        body, _ := io.ReadAll(res.Body)
        return "", fmt.Errorf("onyx error (status %d): %s", res.StatusCode, string(body))
    }

    var resp struct {
        Message      string `json:"message"`
        TopDocuments []struct {
            Content string `json:"blurb"`  // CRITICAL: Use "blurb" not "content"
        } `json:"top_documents"`
    }

    if err := json.NewDecoder(res.Body).Decode(&resp); err != nil {
        return "", err
    }

    // Extract document content
    var docContent string
    for _, doc := range resp.TopDocuments {
        docContent += doc.Content + "\n---\n"
    }

    // Return combined message + docs
    return resp.Message + "\n\nSource Documents:\n---\n" + docContent, nil
}
```

### Key Implementation Notes

1. **Field Mapping**: Always use `blurb` for document content, not `content`
2. **Timeout**: Set reasonable timeout (60s+) for RAG queries
3. **Error Handling**: Check both HTTP status and `error_msg` field
4. **Context Building**: Combine `message` and `top_documents` for full RAG context

---

## Rate Limiting & Performance

- **Concurrent Requests**: Onyx can handle ~10-20 concurrent requests per instance
- **Query Latency**: Expect 5-15 seconds for complex RAG queries
- **Indexing Time**: Allow 30-60 seconds per file for initial indexing
- **Token Limits**: Default context window is ~8K tokens (configurable)

---

## Error Codes Reference

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 403 | Access denied | API user lacks permissions | Fix DB ownership (see troubleshooting guide) |
| 404 | Not found | Invalid endpoint or resource | Check API path and resource ID |
| 400 | Bad request | Missing required fields | Add `chat_session_info` or validate payload |
| 500 | Internal error | Server-side issue | Check Onyx logs |

---

## Testing & Validation

### Quick Health Check
```bash
curl -s http://localhost:3000/health | jq '.'
```

### Validate API Key
```bash
curl -s -X POST "http://localhost:3000/api/chat/send-chat-message" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "stream": false}' | jq '.error_msg'
```

### Check File Indexing Status
```bash
curl -s -X GET "http://localhost:3000/api/user/projects/files/1" \
  -H "Authorization: Bearer $ONYX_KEY" | \
  jq '.[] | select(.status != "COMPLETED") | {name, status, chunk_count}'
```
