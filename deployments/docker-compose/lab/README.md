# LLM Playground Docker Compose Deployment

## 📁 Directory Structure

```
deployments/docker-compose/lab/
├── docker-compose.yml              # Base services (Ollama, Qdrant, AnythingLLM)
├── scripts/                        # Helper scripts
│   ├── start.sh                   # Quick start script
│   ├── stop.sh                    # Stop script
│   └── backup.sh                  # Volume backup script
├── TROUBLESHOOTING.md             # Common issues and solutions
├── ONYX_ARCHITECTURE.md           # Onyx architecture documentation
└── README.md                      # This file
```

This directory contains Docker Compose configurations for running a complete LLM development environment with local Ollama and vector databases.

## 🎯 Quick Start

### Start Base Services (Ollama, Qdrant, AnythingLLM)

```bash
docker compose -f docker-compose.yml up -d
```

### Onyx RAG Platform (Optional)

> **Note**: For Onyx, use the official deployment instead of a custom integration.
> The official deployment has properly configured Vespa schemas and avoids file upload issues.

```bash
# Clone official Onyx repository
git clone --depth 1 https://github.com/onyx-dot-app/onyx.git ~/onyx

# Navigate to deployment directory
cd ~/onyx/deployment/docker_compose

# Follow official Onyx setup instructions
# See: https://docs.onyx.app/deployment/local/docker
```

### Access Services

Once all services are running:

| Service | URL | Description |
|---------|-----|-------------|
| **AnythingLLM** | http://localhost:3001 | Simple document chat with Ollama integration |
| **Onyx** (if installed) | http://localhost:3000 | Advanced RAG platform with agents & connectors |
| Ollama API | http://localhost:11434 | LLM inference server |
| Qdrant | http://localhost:6333 | Vector database |

## 📦 Services Overview

### Base Stack (`docker-compose.yml`)

- **Ollama**: Local LLM inference (Llama, Mistral, etc.)
  - GPU support enabled by default
  - Accessible at `http://localhost:11434`

- **Qdrant**: Vector database for embeddings
  - Web UI at `http://localhost:6333/dashboard`
  - Used by AnythingLLM for document storage

- **AnythingLLM**: Simple document chat interface
  - Easy file upload and chat
  - Integrates with Ollama and Qdrant
  - Access at `http://localhost:3001`

- **Open-WebUI**: Basic chat UI (disabled by default)
  - Enable with `--profile optional`
  - Access at `http://localhost:3002`

### Onyx (Separate Deployment)

For advanced RAG features like agents, web search, and multiple connectors, use the official Onyx deployment:

```bash
git clone --depth 1 https://github.com/onyx-dot-app/onyx.git ~/onyx
cd ~/onyx/deployment/docker_compose
docker compose up -d
```

See `ONYX_ARCHITECTURE.md` for integration details.

## 🛠️ Helper Scripts

### start.sh - Quick Start

Starts base services:

```bash
./scripts/start.sh
```

### stop.sh - Interactive Stop

Stops services with options:

```bash
./scripts/stop.sh
```

### backup.sh - Data Backup

Backs up base stack data volumes:

```bash
./scripts/backup.sh
```

Creates timestamped backups in `backups/` directory.

## 🚀 Common Commands

### Start Everything

```bash
docker compose -f docker-compose.yml -f docker-compose.onyx.yml up -d
```

### Stop Onyx (keep base services running)

```bash
docker compose -f docker-compose.onyx.yml down
```

### View Logs

```bash
# All Onyx services
docker compose -f docker-compose.onyx.yml logs -f

# Specific service
docker compose -f docker-compose.onyx.yml logs -f onyx-api
```

### Check Service Health

```bash
docker compose -f docker-compose.yml -f docker-compose.onyx.yml ps
```

### Restart Services

```bash
# Restart specific service
docker compose -f docker-compose.onyx.yml restart onyx-api

# Restart all Onyx services
docker compose -f docker-compose.onyx.yml restart
```

### Clean Up

```bash
# Stop and remove containers (keeps volumes/data)
docker compose -f docker-compose.yml -f docker-compose.onyx.yml down

# Remove everything including volumes (⚠️ deletes data)
docker compose -f docker-compose.yml -f docker-compose.onyx.yml down -v
```

## ⚙️ Configuration

### Using Ollama (Default - Recommended)

The default `.env.example` is configured to use Ollama from the base stack. No changes needed!

```bash
cp config/.env.example .env
docker compose -f docker-compose.yml up -d          # Start Ollama
docker compose -f docker-compose.onyx.yml up -d     # Start Onyx
```

In Onyx UI:
1. Go to Settings → LLM Providers
2. Add Ollama provider: `http://ollama:11434`
3. Select your model (pull models first with `docker exec ollama ollama pull llama2`)

### Using OpenAI/Anthropic

Edit `.env`:

```bash
# For OpenAI
GEN_AI_MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
GEN_AI_API_VERSION=gpt-4

# For embeddings (optional, local is free)
EMBEDDING_PROVIDER_TYPE=openai
```

### Enable Web Search

Add API keys to `.env`:

```bash
# Option 1: Bing
BING_API_KEY=your-bing-key

# Option 2: Google Custom Search
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your-cse-id
GOOGLE_CUSTOM_SEARCH_API_KEY=your-google-key
```

### Enable Optional Features

```bash
# Code interpreter
CODE_INTERPRETER_BETA_ENABLED=true

# Image generation (requires OpenAI key)
ENABLE_IMAGE_GENERATION=true
```

## 🐛 Troubleshooting

### Onyx API won't start

Check database is ready:
```bash
docker compose -f docker-compose.onyx.yml logs onyx-db
docker compose -f docker-compose.onyx.yml restart onyx-api
```

### GPU not detected

Ensure nvidia-container-toolkit is installed:
```bash
# Check GPU is available
nvidia-smi

# Test in Docker
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### Can't connect to Ollama from Onyx

Verify shared network:
```bash
docker network inspect llm-network
# Should show both ollama and onyx services
```

Test connectivity:
```bash
docker exec onyx-api curl http://ollama:11434/api/version
```

### Port conflicts

If port 3000 is in use, change Onyx port in `.env`:
```bash
ONYX_PORT=3002
```

### Services using too much memory

Reduce model cache sizes or disable model servers (use external LLM only):
```bash
DISABLE_MODEL_SERVER=true
```

## 📚 Next Steps

1. **First time setup**:
   - Create an admin account at http://localhost:3000
   - Configure LLM provider (Ollama recommended)
   - Test chat functionality

2. **Add documents**:
   - Create a workspace
   - Install connectors (Google Drive, Notion, etc.)
   - Or upload files directly

3. **Create agents**:
   - Go to Agents section
   - Define custom instructions
   - Add web search or code interpreter tools
   - Assign knowledge sources

4. **Explore features**:
   - Try deep research mode
   - Set up scheduled document syncs
   - Configure user permissions

## 📖 Documentation

- [Onyx Official Docs](https://docs.onyx.app)
- [Ollama Model Library](https://ollama.ai/library)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

## 🔧 Advanced

### Custom Network Configuration

Both stacks share the `llm-network` bridge network, allowing Onyx to communicate with Ollama, Qdrant, etc.

### Volume Management

Data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls | grep -E "(onyx|ollama|qdrant|anythingllm)"

# Backup a volume
docker run --rm -v onyx_db_data:/data -v $(pwd):/backup alpine tar czf /backup/onyx-db-backup.tar.gz -C /data .

# Restore a volume
docker run --rm -v onyx_db_data:/data -v $(pwd):/backup alpine tar xzf /backup/onyx-db-backup.tar.gz -C /data
```

### Enable Open-WebUI

If you want to use Open-WebUI alongside Onyx:

```bash
docker compose --profile optional -f docker-compose.yml up -d open-webui
```

Access at http://localhost:3002
