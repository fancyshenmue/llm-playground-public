# Makefile for llm-playground Operations
export DATA_SCALE ?= 100000
.DEFAULT_GOAL := help
.PHONY: help langgraph-db-up langgraph-db-down phoenix-up phoenix-down langfuse-up langfuse-down langchain-lab-dev langchain-api-dev langgraph-enterprise-api-dev langgraph-agent graphrag-db-up graphrag-db-down graphrag-generate-data graphrag-seed-postgres graphrag-neo4j-clean graphrag-postgres-clean graphrag-data-clean graphrag-clean-all graphrag-verify

help: ## Display this help screen
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------
# Infrastructure Management
# ---------------------------------------------------------

langgraph-db-up: ## Start PostgreSQL (pgvector) container
	@echo "Starting PostgreSQL (pgvector) container..."
	docker compose -f deployments/docker-compose/langgraph/postgres-pgvector.yml up -d

langgraph-db-down: ## Stop PostgreSQL (pgvector) container
	@echo "Stopping PostgreSQL (pgvector) container..."
	docker compose -f deployments/docker-compose/langgraph/postgres-pgvector.yml down

phoenix-up: ## Start Arize Phoenix Telemetry Stack
	@echo "Starting Arize Phoenix Telemetry Stack..."
	docker compose -f deployments/docker-compose/arizephoenix/docker-compose.yml up -d

phoenix-down: ## Stop Arize Phoenix Telemetry Stack
	@echo "Stopping Arize Phoenix Telemetry Stack..."
	docker compose -f deployments/docker-compose/arizephoenix/docker-compose.yml down

langfuse-up: ## Start Langfuse Telemetry Stack
	@echo "Starting Langfuse Telemetry Stack..."
	docker compose -f deployments/docker-compose/langfuse/docker-compose.yml up -d

langfuse-down: ## Stop Langfuse Telemetry Stack
	@echo "Stopping Langfuse Telemetry Stack..."
	docker compose -f deployments/docker-compose/langfuse/docker-compose.yml down

# ---------------------------------------------------------
# LangChain Services (from documents/langchain/operations.md)
# ---------------------------------------------------------

autocoder-lab-dev: ## Start Autocoder Lab Frontend (React) on Port 5173
	@echo "Starting Autocoder Lab Frontend (React)..."
	pixi run lab-dev

langchain-api-dev: ## Start LangChain Backend API (FastAPI) on Port 8000
	@echo "Starting LangChain Backend API (FastAPI)..."
	pixi run api-dev

# ---------------------------------------------------------
# LangGraph Services (from documents/langgraph/operations.md)
# ---------------------------------------------------------

langgraph-enterprise-api-dev: ## Start LangGraph Enterprise API on Port 8001
	@echo "Starting LangGraph Enterprise API..."
	pixi run enterprise-api-dev

langgraph-agent: ## Display command to run the real-world MCP CLI Agent
	@echo "To run the real-world MCP CLI Agent, use:"
	@echo 'pixi run agent "your prompt here"'

langgraph-autocoder: ## Display command to run the Phase 09 Autonomous Loop
	@echo "To run the Phase 09 Autonomous Coder, use:"
	@echo 'pixi run autocoder "your prompt here"'

# ---------------------------------------------------------
# GraphRAG Dual-Database Services (Phase 12)
# ---------------------------------------------------------

graphrag-db-up: ## Start PostgreSQL and Neo4j for GraphRAG
	@echo "Starting Dual-Database Cluster (PostgreSQL + Neo4j)..."
	docker compose -f deployments/docker-compose/graphrag-ecommerce/docker-compose.yml up -d
	@echo "Databases are starting up on ports 5432 and 7474/7687"

graphrag-db-down: ## Stop PostgreSQL and Neo4j
	@echo "Stopping Dual-Database Cluster..."
	docker compose -f deployments/docker-compose/graphrag-ecommerce/docker-compose.yml down

graphrag-generate-data: ## Generate 100K Retail Products & CRM NdJSON
	@echo "Running Phase 13 Hybrid Python Data Generator..."
	pixi run python scripts/ecommerce-graphrag/hybrid_amazon_generator.py

graphrag-seed-postgres: ## Load Retail NdJSON into PostgreSQL
	@echo "Seeding PostgreSQL with Retail Data (This may take a minute for 1.6M rows)..."
	pixi run python scripts/ecommerce-graphrag/seed_postgres.py

graphrag-backend-dev: ## Start GraphRAG E-Commerce Backend API on Port 8000
	@echo "Starting GraphRAG Backend API (FastAPI)..."
	cd backend/ecommerce-graphrag && pixi run uvicorn main:app --reload --port 8000

graphrag-backend-kill: ## Forcefully kill the GraphRAG Backend API
	@echo "Killing process on port 8000..."
	lsof -ti:8000 | xargs kill -9 || echo "No backend running."

graphrag-frontend-dev: ## Start GraphRAG E-Commerce Frontend on Port 3000
	@echo "Starting GraphRAG Frontend (Next.js)..."
	cd frontend/graphrag-ecommerce && pixi run npm run dev

graphrag-etl: ## Run the Async Product Extraction & Neo4j Ingestion Pipeline
	@echo "Starting Enterprise ETL Pipeline (Extracting Product Entities -> Neo4j)..."
	pixi run python backend/ecommerce-graphrag/ingestion/async_fetch.py

graphrag-neo4j-clean: ## Wipe all Neo4j nodes and relationships for a fresh ETL run
	@echo "Cleaning Neo4j database (DETACH DELETE all nodes)..."
	pixi run python -c "import sys,os; sys.path.append(os.path.join('backend','ecommerce-graphrag')); from core.database import get_neo4j_graph; g=get_neo4j_graph(); g.query('MATCH (n) DETACH DELETE n'); g.query('DROP INDEX product_hybrid_index IF EXISTS'); print('Neo4j cleaned. Ready for fresh ETL.')"
	@echo "Neo4j cleaned."

graphrag-postgres-clean: ## Wipe all PostgreSQL tables for a fresh seed
	@echo "Cleaning PostgreSQL tables..."
	pixi run python -c "import sys,os; sys.path.append(os.path.join('scripts','ecommerce-graphrag')); import seed_postgres; import psycopg; conn = psycopg.connect(seed_postgres.CONN_STR); cur = conn.cursor(); cur.execute(seed_postgres.DDL); conn.commit(); print('PostgreSQL tables wiped.')"

graphrag-data-clean: ## Delete the generated 1.6M JSONL records
	@echo "Deleting generated JSONL files..."
	rm -rf scripts/ecommerce-graphrag/data/*.jsonl

graphrag-clean-all: graphrag-neo4j-clean graphrag-postgres-clean graphrag-data-clean ## Fully wipe GraphRAG DBs and generated data

graphrag-verify: ## Verify PostgreSQL and Neo4j end-to-end topology health
	@echo "Running GraphRAG Enterprise verification..."
	pixi run python .agent/skills/graphrag-verify/scripts/verify_pipeline.py

graphrag-rebuild: graphrag-neo4j-clean graphrag-etl ## Full rebuild: clean Neo4j → run ETL (assumes diverse data is already seeded)

# ---------------------------------------------------------
# Ollama Local Service (via Pixi/Launchctl)
# ---------------------------------------------------------

ollama-start: ## Start the local Ollama background service
	@echo "Starting Ollama daemon..."
	pixi run ollama-daemon-start

ollama-stop: ## Stop the local Ollama background service
	@echo "Stopping Ollama daemon..."
	pixi run ollama-daemon-stop

ollama-restart: ## Restart the local Ollama background service
	@echo "Restarting Ollama daemon..."
	pixi run ollama-daemon-stop
	pixi run ollama-daemon-start

ollama-logs: ## Tail the local Ollama service logs
	pixi run ollama-daemon-logs
