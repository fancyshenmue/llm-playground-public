# Onyx Architecture & LLM Integration Guide

## Onyx is Completely Independent ✅

**Key Concept:** Onyx does NOT depend on Ollama or any specific LLM service.

### Onyx Core Architecture

```
Onyx Standalone Services (Full Functionality)
├── onyx-api          # Backend API server
├── onyx-background   # Background job processor
├── onyx-web          # Frontend web interface
├── onyx-db           # PostgreSQL database
├── onyx-index        # Vespa hybrid search engine
├── onyx-cache        # Redis cache
├── onyx-minio        # S3-compatible object storage
├── onyx-inference    # Built-in inference server (embeddings) ✅
└── onyx-indexing     # Built-in indexing server (embeddings) ✅
```

**Key Point:** Onyx includes its own embedding model servers and can handle document indexing and search independently.

#### Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        User[User Browser] --> Nginx[Nginx Reverse Proxy<br/>:3000]
    end

    subgraph "Application Layer"
        Nginx --> Web[Onyx Web<br/>Next.js Frontend]
        Nginx --> API[Onyx API<br/>FastAPI Backend<br/>:8080]
        API --> BG[Background Worker<br/>Job Processing]
    end

    subgraph "AI/ML Layer"
        BG --> INF[Inference Server<br/>Embeddings<br/>GPU]
        BG --> IDX[Indexing Server<br/>Document Processing<br/>GPU]
    end

    subgraph "Data Layer"
        API --> DB[(PostgreSQL<br/>Metadata)]
        API --> Vespa[(Vespa<br/>Hybrid Search)]
        API --> Redis[(Redis<br/>Cache)]
        API --> MinIO[(MinIO<br/>S3 Storage)]
    end

    subgraph "Optional: External LLM"
        API -.->|Optional| Ollama[Ollama<br/>Local LLM]
        API -.->|Optional| OpenAI[OpenAI API<br/>Cloud LLM]
        API -.->|Optional| Anthropic[Anthropic API<br/>Cloud LLM]
    end

    style INF fill:#ff6b6b,color:#fff
    style IDX fill:#ff6b6b,color:#fff
    style Ollama fill:#4ecdc4,color:#fff
    style OpenAI fill:#4ecdc4,color:#fff
    style Anthropic fill:#4ecdc4,color:#fff
    style Nginx fill:#45b7d1,color:#fff
```

## LLM Integration Options (Optional)

Onyx supports multiple LLM providers - you can choose any one:

### Integration Scenarios Overview

```mermaid
graph LR
    subgraph "Scenario 1: Onyx + Ollama"
        O1[Onyx Services] -->|LLM Requests| OL[Ollama<br/>Local]
        O1 -->|Embeddings| O1E[Built-in Servers]
    end

    subgraph "Scenario 2: Onyx + OpenAI"
        O2[Onyx Services] -->|LLM Requests| OAI[OpenAI API<br/>Cloud]
        O2 -->|Embeddings| O2E[Built-in Servers]
    end

    subgraph "Scenario 3: Onyx + Anthropic"
        O3[Onyx Services] -->|LLM Requests| ANT[Anthropic API<br/>Cloud]
        O3 -->|Embeddings| O3E[Built-in Servers]
    end

    subgraph "Scenario 4: Onyx Standalone"
        O4[Onyx Services] -->|Embeddings Only| O4E[Built-in Servers]
        O4 -.->|No Chat| X[❌]
    end

    style OL fill:#4ecdc4,color:#fff
    style OAI fill:#4ecdc4,color:#fff
    style ANT fill:#4ecdc4,color:#fff
    style O1E fill:#ff6b6b,color:#fff
    style O2E fill:#ff6b6b,color:#fff
    style O3E fill:#ff6b6b,color:#fff
    style O4E fill:#ff6b6b,color:#fff
```

### Option 1: Use Ollama (Local, Free)

**Pros:**
- 🆓 Completely free
- 🏠 Runs locally, data privacy
- 🚀 Integrates with your existing Ollama

**Configuration:**
```bash
# config/.env
GEN_AI_MODEL_PROVIDER=ollama
GEN_AI_LLM_PROVIDER_TYPE=ollama
GEN_AI_API_ENDPOINT=http://ollama:11434
```

**Startup:**
```bash
# Start Ollama first
docker compose -f docker-compose.yml up -d ollama

# Then start Onyx
docker compose -f docker-compose.onyx.yml up -d
```

### Option 2: Use OpenAI (Cloud, Paid)

**Pros:**
- 🌐 No local GPU needed
- 🎯 Latest GPT models
- ⚡ Fast response

**Configuration:**
```bash
# config/.env
GEN_AI_MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
GEN_AI_API_VERSION=gpt-4
```

**Startup:**
```bash
# Only start Onyx (no Ollama needed)
docker compose -f docker-compose.onyx.yml up -d
```

### Option 3: Use Anthropic Claude (Cloud, Paid)

**Configuration:**
```bash
# config/.env
GEN_AI_MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-api-key-here
```

### Option 4: Use Only Onyx Built-in Servers (Embeddings Only)

**Use Case:** Document search only, no chat functionality needed

**Configuration:**
```bash
# config/.env
# Don't configure any external LLM
DISABLE_MODEL_SERVER=false  # Use built-in embedding servers
```

**Features:**
- ✅ Document upload and indexing
- ✅ Semantic search
- ✅ Hybrid search (BM25 + Dense + Sparse)
- ❌ Chat generation (requires external LLM)

## Network Architecture Explained

### Current Configuration (Two Networks):

```yaml
networks:
  llm-network:      # Shared network (optional)
    external: true  # Connects to Ollama (if used)

  onyx-internal:    # Onyx internal network (required)
    driver: bridge  # Communication between Onyx services
```

#### Network Topology Diagram

```mermaid
graph TB
    subgraph "External Access"
        User[User Browser<br/>localhost:3000]
    end

    subgraph "llm-network - Shared/Optional"
        Ollama[Ollama<br/>:11434]
        Qdrant[Qdrant<br/>:6333]
        ANY[AnythingLLM<br/>:3001]
    end

    subgraph "onyx-internal - Private"
        subgraph "Entry"
            Nginx[Nginx<br/>:80→3000]
        end

        subgraph "App"
            Web[Onyx Web]
            API[Onyx API<br/>:8080]
            BG[Background]
        end

        subgraph "AI/ML"
            INF[Inference<br/>GPU]
            IDX[Indexing<br/>GPU]
        end

        subgraph "Data"
            DB[("PostgreSQL")]
            Vespa[("Vespa")]
            Redis[("Redis")]
            MinIO[("MinIO")]
        end
    end

    User --> Nginx
    Nginx --> Web
    Nginx --> API
    API --> BG
    API --> DB
    API --> Vespa
    API --> Redis
    API --> MinIO
    BG --> INF
    BG --> IDX

    API -.->|Optional| Ollama
    API -.->|Optional| Qdrant

    style User fill:#95e1d3,color:#000
    style Nginx fill:#45b7d1,color:#fff
    style Ollama fill:#4ecdc4,color:#fff
    style INF fill:#ff6b6b,color:#fff
    style IDX fill:#ff6b6b,color:#fff
```

### Network Usage Scenarios:

**Scenario 1: Using Ollama**
- Onyx services join both `llm-network` and `onyx-internal`
- Can access `ollama:11434`

**Scenario 2: Standalone (OpenAI/Anthropic)**
- Onyx services only need `onyx-internal`
- Access external APIs via internet

**Scenario 3: Completely Offline (Built-in Servers Only)**
- Onyx services only need `onyx-internal`
- No external connections needed

## Optional: Remove llm-network Dependency

If you want Onyx to be completely independent, you can simplify:

### Simplified docker-compose.onyx.yml

```yaml
services:
  onyx-api:
    networks:
      - onyx-internal  # Only use internal network

  onyx-background:
    networks:
      - onyx-internal

networks:
  onyx-internal:
    driver: bridge
  # Remove llm-network (if not using Ollama)
```

## Usage Recommendations

### 🎯 Recommended Configuration (Maximum Flexibility)

Keep current configuration:
- ✅ Both networks configured
- ✅ Choose LLM provider in `.env`
- ✅ Start only Onyx when Ollama not needed

### Startup Commands Comparison:

**With Ollama:**
```bash
docker compose -f docker-compose.yml -f docker-compose.onyx.yml up -d
```

**Without Ollama (Standalone):**
```bash
# Start only Onyx
docker compose -f docker-compose.onyx.yml up -d

# Configure OpenAI or Anthropic
cp config/.env.example .env
nano .env  # Set OPENAI_API_KEY or ANTHROPIC_API_KEY
```

## FAQ

### Q: Does Onyx require GPU?
**A:** No, it's optional.
- Onyx model servers can run on CPU (slower)
- Can disable built-in model servers: `DISABLE_MODEL_SERVER=true`
- Cloud LLMs (OpenAI/Anthropic) don't need local GPU

### Q: Can I use both Ollama and OpenAI?
**A:** Yes! Onyx UI allows configuring multiple LLM providers and switching between them dynamically.

### Q: Can Onyx run without any LLM?
**A:** Yes, but with limited functionality:
- ✅ Document upload and search
- ✅ Connector sync (Google Drive, Notion, etc.)
- ❌ Chat features (requires LLM)
- ❌ Agents (requires LLM)

## Summary

| Running Mode | Onyx Standalone | Needs Ollama | Needs Internet | Cost |
|--------------|-----------------|--------------|----------------|------|
| **Onyx + Ollama** | ✅ | ✅ | ❌ | Free |
| **Onyx + OpenAI** | ✅ | ❌ | ✅ | Paid |
| **Onyx + Anthropic** | ✅ | ❌ | ✅ | Paid |
| **Onyx Search Only** | ✅ | ❌ | ❌ | Free |

**Conclusion:** Onyx is a completely independent service. Ollama is just one of many LLM options!
