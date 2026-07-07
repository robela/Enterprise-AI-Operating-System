# Enterprise AI Operating System

A generic AI-enabled enterprise platform supporting multiple industries (Healthcare, Banking, Government, Airlines, Insurance, Education, Telecommunications).

## Features

- Multi-tenant SaaS
- AI Agents (Orchestrator, Knowledge, Validation, Translation)
- RAG (Retrieval-Augmented Generation) Pipeline
- Workflow Automation with Human-in-the-Loop
- Event-Driven Architecture
- Audit & Compliance (immutable logs)
- API-First (REST, GraphQL, WebSocket, gRPC)
- Cloud and On-Prem Deployment

## Architecture

- **Domain-Driven Design (DDD)** — business logic is isolated in domains
- **Hexagonal Architecture** — all external dependencies behind ports/adapters
- **Provider-Agnostic AI** — OpenAI, Azure OpenAI, Gemini, Ollama, Anthropic

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI |
| ORM | SQLAlchemy + Alembic |
| Database | PostgreSQL |
| Cache | Redis |
| Search | Elasticsearch |
| Vector Store | pgvector / Qdrant |
| Messaging | Kafka / RabbitMQ |
| Observability | OpenTelemetry + Prometheus + Grafana |
| Auth | OAuth2 + JWT + RBAC/ABAC |
| Deployment | Docker, Kubernetes, Helm, Terraform |

## Quick Start

```bash
# Clone and enter
cd Enterprise-AI-Operating-System

# Copy environment config
cp .env.example .env

# Start all services
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head

# Access API docs
open http://localhost:8000/docs
```

## Project Structure

```
backend/
├── app/          # FastAPI application factory
├── core/         # Config, security, logging, middleware, DB, cache, events
├── domains/      # DDD domains (users, identity, organizations, documents, …)
├── ai/           # Provider-agnostic AI layer (agents, RAG, embeddings, …)
├── infrastructure/ # Persistence, messaging, storage, search, monitoring
├── api/          # REST, GraphQL, WebSocket, gRPC entry points
├── workflows/    # BPMN-style workflow engine
├── workers/      # Background job workers
├── tests/        # Unit and integration tests
└── deployment/   # Docker, Kubernetes, Terraform, Helm
```

## Running Tests

```bash
pytest backend/tests/ -v
```

## Environment Variables

See `.env.example` for all required variables.
