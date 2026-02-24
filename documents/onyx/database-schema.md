# Onyx Database Schema Reference

## Overview
Onyx uses PostgreSQL for metadata storage and Vespa for vector search. This document covers the PostgreSQL schema relevant to RAG integration.

---

## Core Tables

### `user` Table
Stores user account information.

**Schema**:
```sql
CREATE TABLE "user" (
    id UUID PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    hashed_password VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Key Points**:
- Each user has a unique UUID
- Email serves as the primary identifier
- API users have emails like `api_key__<name>@<uuid>onyxapikey.ai`

---

### `api_key` Table
Stores API key credentials and ownership.

**Schema**:
```sql
CREATE TABLE api_key (
    id SERIAL PRIMARY KEY,
    hashed_api_key VARCHAR NOT NULL,
    api_key_display VARCHAR,
    user_id UUID NOT NULL,        -- The identity this key operates as
    owner_id UUID NOT NULL,        -- The admin who created this key
    created_at TIMESTAMP DEFAULT NOW(),
    name VARCHAR
);
```

**Critical Fields**:
- `user_id`: The **service account** identity created for this API key
- `owner_id`: The **admin user** who generated the key
- These are usually DIFFERENT UUIDs!

**Common Query**:
```sql
-- Find API key details
SELECT id, user_id, owner_id, name
FROM api_key
WHERE name = 'admin-api-key';
```

---

### `user_project` Table
Stores user-created projects (folders/workspaces).

**Schema**:
```sql
CREATE TABLE user_project (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES "user"(id)
);
```

**Key Points**:
- Projects are owned by a single user
- Project name must be unique per user
- Common issue: API key's `user_id` doesn't match project's `user_id`

**Common Queries**:
```sql
-- List all projects
SELECT id, name, user_id FROM user_project;

-- Find project by name
SELECT id, user_id FROM user_project WHERE name = 'pinescript-v6';

-- Update ownership
UPDATE user_project
SET user_id = '79a33dce-0c6b-44cf-a420-a3659b94528c'
WHERE id = 1;
```

---

### `user_file` Table
Stores uploaded file metadata.

**Schema**:
```sql
CREATE TABLE user_file (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    name VARCHAR(255) NOT NULL,
    file_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    link_url VARCHAR,
    file_type VARCHAR,
    content_type VARCHAR,
    status VARCHAR(10) DEFAULT 'PROCESSING',
    token_count INTEGER,
    chunk_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    needs_project_sync BOOLEAN DEFAULT false,
    last_project_sync_at TIMESTAMP WITH TIME ZONE,
    document_id_migrated BOOLEAN DEFAULT true
);
```

**Critical Fields**:
- `status`: "PROCESSING" → "COMPLETED" → "FAILED"
- `chunk_count`: NULL until Vespa indexing completes
- `user_id`: Owner of the file (MUST match for API access)
- `document_id`: Used for Vespa document retrieval

**Status Flow**:
```
UPLOAD → PROCESSING (chunking) → COMPLETED (indexed) → FAILED (error)
```

**Common Queries**:
```sql
-- Check file status
SELECT id, name, status, chunk_count, user_id
FROM user_file
WHERE name LIKE '%pitfalls%';

-- Update ownership for project files
UPDATE user_file
SET user_id = '79a33dce-0c6b-44cf-a420-a3659b94528c'
FROM project__user_file
WHERE user_file.id = project__user_file.user_file_id
AND project__user_file.project_id = 1;

-- Find unindexed files
SELECT name, status, chunk_count
FROM user_file
WHERE status = 'COMPLETED' AND chunk_count IS NULL;
```

---

### `project__user_file` Table
Junction table linking projects to files.

**Schema**:
```sql
CREATE TABLE project__user_file (
    project_id INTEGER NOT NULL,
    user_file_id UUID NOT NULL,
    PRIMARY KEY (project_id, user_file_id),
    FOREIGN KEY (project_id) REFERENCES user_project(id),
    FOREIGN KEY (user_file_id) REFERENCES user_file(id)
);
```

**Key Points**:
- Many-to-many relationship
- A file can be in multiple projects
- A project can have many files

**Common Queries**:
```sql
-- List all files in a project
SELECT uf.id, uf.name, uf.status, uf.chunk_count
FROM user_file uf
JOIN project__user_file pf ON uf.id = pf.user_file_id
WHERE pf.project_id = 1;

-- Add file to project
INSERT INTO project__user_file (project_id, user_file_id)
VALUES (1, 'file-uuid-here');

-- Remove file from project
DELETE FROM project__user_file
WHERE project_id = 1 AND user_file_id = 'file-uuid';
```

---

## Permission Model

### Identity Flow

```
Admin User (web UI)
    ↓ creates
API Key
    ↓ generates
Service Account User (auto-created)
    ↓ operates as
API Requests
```

### Access Control Rules

1. **Project Access**: `user_id` of project MUST match `user_id` of API key
2. **File Access**: `user_id` of file MUST match `user_id` in request context
3. **No Inheritance**: Service accounts don't inherit admin permissions

### Common Permission Fix

```sql
-- Get IDs
SELECT id, email FROM "user" WHERE email LIKE '%gmail%';  -- Admin
SELECT user_id, owner_id FROM api_key WHERE id = 1;      -- API key

-- Align API key to admin
UPDATE api_key
SET user_id = '79a33dce-0c6b-44cf-a420-a3659b94528c'  -- Admin UUID
WHERE id = 1;

-- Align project ownership
UPDATE user_project
SET user_id = '79a33dce-0c6b-44cf-a420-a3659b94528c'
WHERE id = 1;

-- Align file ownership
UPDATE user_file
SET user_id = '79a33dce-0c6b-44cf-a420-a3659b94528c'
WHERE id IN (
    SELECT user_file_id FROM project__user_file WHERE project_id = 1
);
```

---

## Vespa Integration

### Document Storage
- PostgreSQL stores **metadata** (filename, status, ownership)
- Vespa stores **content** (chunks, embeddings, text)
- `document_id` field links PostgreSQL → Vespa

### Indexing Pipeline
```
File Upload → PostgreSQL (metadata)
    → Background worker (chunking)
    → Vespa (indexing)
    → PostgreSQL (update chunk_count)
```

### Monitoring
```sql
-- Find files pending indexing
SELECT name, status, created_at
FROM user_file
WHERE status = 'PROCESSING'
ORDER BY created_at DESC;

-- Check indexing stats
SELECT
    status,
    COUNT(*) as count,
    AVG(chunk_count) as avg_chunks,
    AVG(token_count) as avg_tokens
FROM user_file
WHERE chunk_count IS NOT NULL
GROUP BY status;
```

---

## Useful Diagnostic Queries

### Check User Association
```sql
SELECT
    u.email,
    up.name as project,
    uf.name as file,
    uf.status,
    uf.chunk_count
FROM "user" u
LEFT JOIN user_project up ON u.id = up.user_id
LEFT JOIN project__user_file puf ON up.id = puf.project_id
LEFT JOIN user_file uf ON puf.user_file_id = uf.id
WHERE u.email = 'your-email@example.com';
```

### Find Orphaned Files
```sql
SELECT uf.id, uf.name, uf.created_at
FROM user_file uf
LEFT JOIN project__user_file puf ON uf.id = puf.user_file_id
WHERE puf.user_file_id IS NULL;
```

### Project Health Check
```sql
SELECT
    up.id,
    up.name,
    COUNT(puf.user_file_id) as file_count,
    SUM(CASE WHEN uf.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN uf.chunk_count > 0 THEN 1 ELSE 0 END) as indexed
FROM user_project up
LEFT JOIN project__user_file puf ON up.id = puf.project_id
LEFT JOIN user_file uf ON puf.user_file_id = uf.id
GROUP BY up.id, up.name;
```

---

## Migration Notes

If you're migrating from an older Onyx version:
- `document_id_migrated` tracks migration status
- Older schemas may use different field names
- Always check `\d table_name` to verify current schema
