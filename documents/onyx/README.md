# Onyx Integration Documentation

This directory contains comprehensive documentation for integrating Onyx (formerly Danswer) as a RAG provider.

## Documents

### 1. [Quick Start Guide](quick-start.md)
**For**: Getting started quickly
**Contains**:
- Step-by-step setup instructions
- API key generation
- Project creation
- Document upload process
- Basic testing commands
- Common first-time issues and fixes

**Start here** if you're setting up Onyx for the first time.

---

### 2. [Troubleshooting Guide](troubleshooting-guide.md)
**For**: Solving common problems
**Contains**:
- Authentication failure resolution
- Empty RAG context debugging
- Database permission fixes
- Field mapping issues
- Indexing problems
- General debugging workflows

**Use this** when something isn't working as expected.

---

### 3. [API Reference](api-reference.md)
**For**: Implementing API integration
**Contains**:
- Complete endpoint documentation
- Request/response schemas
- Go client implementation examples
- Error codes and handling
- Rate limiting guidance
- Testing and validation commands

**Use this** when writing code to interact with Onyx.

---

### 4. [Database Schema](database-schema.md)
**For**: Understanding data model and permissions
**Contains**:
- PostgreSQL table schemas
- Permission and ownership model
- Common SQL queries
- Vespa integration notes
- Diagnostic queries
- Migration guidance

**Use this** when you need to understand or modify database state.

---

## Common Workflows

### Setting Up RAG for a New Project
1. Follow [Quick Start Guide](quick-start.md) steps 1-6
2. Test with [API Reference](api-reference.md) examples
3. If issues arise, consult [Troubleshooting Guide](troubleshooting-guide.md)

### Debugging Authentication Issues
1. Check [Troubleshooting Guide - Issue 1](troubleshooting-guide.md#issue-1-authentication-failures-403-access-denied)
2. Verify with [Database Schema - Permission Model](database-schema.md#permission-model)
3. Apply fixes from diagnostic queries

### Implementing Custom Integration
1. Review [API Reference - Core Endpoints](api-reference.md#core-endpoints)
2. Check [API Reference - Go Client Implementation](api-reference.md#go-client-implementation)
3. Reference [Database Schema](database-schema.md) for data model understanding

---

## Key Concepts

### Projects vs Personas
- **Projects**: Private, user-scoped document collections
- **Personas**: Public, configurable AI assistants with linked document sets
- **When to use**: Use Projects for user-specific contexts, Personas for shared RAG

### API Authentication
- All requests use `Authorization: Bearer <api-key>` header
- API keys create a separate "service account" user
- Service accounts don't inherit admin permissions automatically

### Document Lifecycle
```
Upload → PROCESSING → Chunking → Vespa Indexing → COMPLETED
```
- Wait for `chunk_count` > 0 before querying
- Typical indexing: 30-60 seconds per file

### Field Mapping
**Critical**: Onyx API uses `blurb` field for document content, NOT `content`
```go
type TopDocument struct {
    Content string `json:"blurb"`  // NOT "content"
}
```

---

## Integration Checklist

### Development
- [ ] Read [Quick Start Guide](quick-start.md)
- [ ] Set up test project with sample documents
- [ ] Implement client using [API Reference](api-reference.md)
- [ ] Test RAG queries with various inputs
- [ ] Handle errors per [Troubleshooting Guide](troubleshooting-guide.md)

### Production
- [ ] Secure API key storage (environment variables, secrets manager)
- [ ] Implement proper error handling and retries
- [ ] Configure timeouts (60s recommended)
- [ ] Add monitoring for query latency
- [ ] Set up alerts for indexing failures
- [ ] Review [Database Schema](database-schema.md) for backup strategy
- [ ] Consider rate limiting and caching

---

## Related Resources

### Internal
- `$HOME/dev/llm-playground/internal/go/api/onyx.go` - Go client implementation
- `$HOME/dev/llm-playground/cmd/go/llm-utils/config.yaml` - Configuration example

### External
- [Onyx Official Documentation](https://docs.onyx.app)
- [GitHub Repository](https://github.com/onyx-dot-app/onyx)
- [Vespa Documentation](https://docs.vespa.ai)

---

## Contributing

If you discover new issues or solutions:
1. Document the problem in [Troubleshooting Guide](troubleshooting-guide.md)
2. Add relevant SQL queries to [Database Schema](database-schema.md)
3. Update API examples in [API Reference](api-reference.md)
4. Keep documentation concise and example-driven

---

## Version History

- **2026-01-17**: Initial documentation created during Pine Script RAG integration
  - Covers Onyx version deployed via official Docker Compose
  - PostgreSQL schema as of January 2026
  - API endpoints validated against `/api/openapi.json`

---

## Quick Command Reference

```bash
# Onyx health check
curl -s http://localhost:3000/health

# List projects
docker exec onyx-relational_db-1 psql -U postgres -d postgres -c "SELECT * FROM user_project;"

# Check file status
curl -X GET "http://localhost:3000/api/user/projects/files/1" \
  -H "Authorization: Bearer $ONYX_KEY" | jq '.[] | {name, status, chunk_count}'

# Test RAG query
curl -X POST "http://localhost:3000/api/chat/send-chat-message" \
  -H "Authorization: Bearer $ONYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "stream": false, "chat_session_info": {"project_id": 1}}' | jq '.top_documents | length'

# View API logs
docker logs onyx-api_server-1 --tail 50 -f
```
