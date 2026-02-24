# Quick Fix: WSL2 Docker Mount Issue

## Problem
When running `docker compose` from **Windows Git Bash**, the nginx container fails with:
```
Error response from daemon: accessing specified distro mount service:
stat /run/guest-services/distro-services/ubuntu-24-04.sock: no such file or directory
```

This happens because:
- Git Bash path translation conflicts with WSL2 Docker Desktop
- Volume mounts like `./config/nginx/onyx.conf` don't resolve correctly
- Docker tries to access WSL2 distro services but path mapping fails

## Solutions

### ✅ Solution 1: Run from WSL (RECOMMENDED)

```bash
# Open WSL Ubuntu terminal
wsl

# Navigate to project
cd $HOME/dev/llm-playground/deployments/docker-compose/lab

# Run docker compose
docker compose -f docker-compose.onyx.yml up -d
```

**Why this works:** Docker Desktop integrates natively with WSL2, paths resolve correctly.

### ⚠️ Solution 2: Fix Path for Git Bash

If you must use Git Bash, you need to use absolute Windows paths:

1. Find your absolute Windows path:
```bash
# In Git Bash
pwd
# Example output: /c/Users/YourName/dev/llm-playground/deployments/docker-compose/lab
```

2. Edit `docker-compose.onyx.yml` line 276:
```yaml
# Change FROM:
volumes:
  - ./config/nginx/onyx.conf:/etc/nginx/conf.d/default.conf:ro

# Change TO (use YOUR actual path):
volumes:
  - /c/Users/YourUsername/dev/llm-playground/deployments/docker-compose/lab/config/nginx/onyx.conf:/etc/nginx/conf.d/default.conf:ro
```

3. Restart:
```bash
docker compose -f docker-compose.onyx.yml down
docker compose -f docker-compose.onyx.yml up -d
```

### 🔧 Solution 3: Temporary - Expose Onyx Without Nginx

For quick testing, you can bypass nginx temporarily by exposing the web server directly.

Edit `docker-compose.onyx.yml`:

```yaml
# Comment out or remove onyx-nginx service entirely

# In onyx-web service, add:
onyx-web:
  image: onyxdotapp/onyx-web-server:latest
  container_name: onyx-web
  ports:
    - "3000:3000"  # Add this line
  # ... rest of config
```

Then access Onyx directly at `http://localhost:3000` (without nginx).

**Note:** This bypasses the reverse proxy but works for testing.

## Current Status

Based on your output, these containers are running:
- ✅ onyx-db (PostgreSQL)
- ✅ onyx-index (Vespa)
- ✅ onyx-cache (Redis)
- ✅ onyx-minio (S3 storage)
- ✅ onyx-inference (GPU embedding server)
- ✅ onyx-indexing (GPU indexing server)
- ✅ onyx-api (Backend API)
- ✅ onyx-background (Background worker)
- ✅ onyx-web (Frontend)
- ❌ onyx-nginx (Failed - mount issue)

**Good news:** The core Onyx services are running! Only nginx failed.

## Recommended Action

1. **Stop current containers:**
```bash
docker compose -f docker-compose.onyx.yml down
```

2. **Run from WSL instead:**
```bash
wsl
cd $HOME/dev/llm-playground/deployments/docker-compose/lab
docker compose -f docker-compose.onyx.yml up -d
```

3. **Verify all services are running:**
```bash
docker compose -f docker-compose.onyx.yml ps
```

4. **Access Onyx:**
```
http://localhost:3000
```

## WSL vs Git Bash Comparison

| Aspect | WSL Ubuntu | Git Bash |
|--------|------------|----------|
| Docker Integration | ✅ Native | ⚠️ Path issues |
| Volume Mounts | ✅ Works | ❌ Requires absolute paths |
| Network | ✅ Seamless | ✅ Works |
| Performance | ✅ Better | ⚠️ Slower (translation layer) |
| **Recommendation** | **Use this** | Avoid for docker-compose |

## Why Use WSL for Docker?

Docker Desktop's WSL2 backend is designed to work with WSL, not Git BasThis guide will be updated as more solutions are discovered.

---

## Issue: Onyx File Upload Fails with Vespa 400 Error

**Symptom:**
- Files fail to upload in Onyx UI with error: "File failed and was removed"
- Backend logs show: `ERROR: Non-retryable HTTP 400 error for document` when writing to Vespa
- All other pipeline steps work (file upload, text extraction, embedding generation)
- Only the final Vespa indexing step fails

**Logs Example:**
```
ERROR: Non-retryable HTTP 400 error for document 'xxx'
httpx.HTTPStatusError: Client error '400 Bad Request' for url
'http://onyx-index:8081/document/v1/default/danswer_chunk/docid/xxx'
```

### Root Cause

This is a **Vespa schema compatibility issue** between Onyx's document format and Vespa's expected schema. The 400 error indicates Vespa is rejecting the document structure sent by Onyx.

### Attempted Solutions (That Didn't Work)

1. ✗ Restarting Vespa container
2. ✗ Adding missing `VESPA_PORT` and `VESPA_TENANT_PORT` environment variables
3. ✗ Complete Vespa data volume reset (`docker volume rm onyx-stack_onyx_vespa_data`)
4. ✗ Full stack restart with fresh Vespa deployment

### Potential Solutions

#### Option 1: Use Official Onyx Deployment (Recommended)

Instead of our custom docker-compose, use the official Onyx deployment:

```bash
# Clone official Onyx repository
git clone --depth 1 https://github.com/onyx-dot-app/onyx.git
cd onyx/deployment/docker_compose

# Use official docker-compose with GPU support
docker compose -f docker-compose.gpu-dev.yaml up -d
```

The official deployment has tested Vespa schema configurations.

#### Option 2: Use AnythingLLM Instead

If you just need document Q&A with local LLMs:

```bash
# AnythingLLM is already in your stack and works perfectly
# Access at http://localhost:3001
# Simpler setup, same Ollama integration, no Vespa complexity
```

#### Option 3: Wait for Onyx Version Update

This may be a version-specific issue. Check:
- [Onyx GitHub Issues](https://github.com/onyx-dot-app/onyx/issues)
- Consider using a specific tagged version instead of `:latest`

### Investigation Commands

```bash
# Check current Onyx and Vespa versions
docker compose -f docker-compose.onyx.yml exec onyx-api python -c "import onyx; print(onyx.__version__)" 2>/dev/null || echo "Version not available"

# Check Vespa schema deployment
docker compose -f docker-compose.onyx.yml exec onyx-api python -c "import urllib.request; print(urllib.request.urlopen('http://onyx-index:19071/application/v2/tenant/default/application/default').read().decode())"

# Monitor realtime upload errors
docker compose -f docker-compose.onyx.yml logs -f onyx-background | grep -i "error\|400"
```

### Current Status

**✅ RESOLVED**: Use the official Onyx deployment instead of custom integration.

### Solution That Works

The official Onyx deployment has properly configured Vespa schemas and avoids all file upload issues:

```bash
# Clone official repository
git clone --depth 1 https://github.com/onyx-dot-app/onyx.git ~/onyx

# Navigate to deployment
cd ~/onyx/deployment/docker_compose

# Start official deployment
docker compose up -d

# Access at http://localhost:3000
```

#### Connecting to Existing Ollama

To use your existing Ollama instance with official Onyx:

**Option 1: Join llm-network (Recommended)**

Add to `docker-compose.yml`:
```yaml
networks:
  default:
    name: llm-network
    external: true
```

Then in Onyx UI:
- LLM Provider: Ollama
- API URL: `http://ollama:11434`

**Option 2: Use host.docker.internal**

In Onyx UI:
- API URL: `http://host.docker.internal:11434`

### Why Custom Integration Failed

The custom `docker-compose.onyx.yml` had:
1. Vespa schema compatibility issues with latest Onyx version
2. Missing or incorrect Vespa environment configurations
3. Document structure mismatches causing 400 errors

The official deployment is tested and maintained by the Onyx team, ensuring all components work together correctly.
- File paths resolve correctly
- Volume mounts work seamlessly
- Better performance (no Windows→Linux path translation)
- Native Linux environment

**TL;DR: Always use WSL Ubuntu for docker-compose commands, not Git Bash!**
