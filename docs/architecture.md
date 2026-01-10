# DocMind — Architecture

## Overview

DocMind is a production-ready RAG (Retrieval-Augmented Generation) system. Users upload documents, the system embeds them into a vector database, and GPT-4o answers questions with inline citations.

```
Browser / Embedded Widget
        │
        ▼
  Gateway (Node.js :3000)
  ├─ JWT cookie auth
  ├─ Rate limiting (Redis)
  ├─ Workspace access check
  └─ Proxy to FastAPI
        │
        ▼
  FastAPI Backend (:8000)
  ├─ Document ingestion API
  ├─ Chat API (SSE streaming)
  ├─ Billing API (Stripe)
  └─ Admin API
        │
   ┌────┴─────────────┐
   ▼                  ▼
PostgreSQL         Celery Worker
(+ pgvector)       ├─ Parse documents
                   ├─ Chunk + embed
                   └─ Store vectors
```

## Services

| Service | Tech | Port | Purpose |
|---------|------|------|---------|
| `frontend` | React 18 + Vite → nginx | 80 | SPA + embeddable widget bundle |
| `gateway` | Node.js + Express | 3000 | Auth, rate limiting, proxy |
| `backend` | FastAPI + Python 3.11 | 8000 | RAG core, REST API |
| `worker` | Celery | — | Async document processing |
| `beat` | Celery Beat | — | Scheduled maintenance tasks |
| `postgres` | PostgreSQL 16 + pgvector | 5432 | Data + vector store |
| `redis` | Redis 7 | 6379 | Session cache, task queue |

## Data Flow

### Document Ingestion
```
Upload/Scrape → Gateway (auth) → FastAPI (validate + S3 upload)
→ Celery task: parse → chunk (1000 tok / 200 overlap) → embed (OpenAI)
→ bulk insert to document_chunks → status=completed
```

### Chat Query (SSE)
```
User message → Gateway (auth + quota check) → FastAPI
→ save user message → embed query → pgvector similarity search (top-8, score>0.7)
→ LangChain: condense question → build prompt → GPT-4o stream
→ emit SSE tokens → parse [SOURCE:id] markers → emit citations event
→ save assistant message + citations → log usage
```

## Database Schema (key tables)

- **users** — auth, profile
- **workspaces** — multi-tenant namespacing
- **workspace_members** — roles: owner | admin | member | viewer
- **documents** — metadata, status, storage key
- **document_chunks** — `embedding vector(1536)`, HNSW index
- **chat_sessions / chat_messages / citations** — conversation history
- **subscriptions** — Stripe subscription per workspace
- **usage_logs** — query/upload events for quota enforcement
- **api_keys** — widget authentication (bcrypt hashed)

## Auth

- **Web app**: httpOnly JWT cookie (access 30min, refresh 30d), verified by gateway
- **Widget**: API key (`dm_live_<hex>`) — gateway validates format, FastAPI verifies bcrypt hash

## Vector Search

pgvector with HNSW index on `document_chunks.embedding`. Queries are workspace-scoped (`WHERE workspace_id = ?`) for tenant isolation. Score threshold: 0.7, top-k: 8.

## Billing

Stripe Checkout + Customer Portal. Plans: Free (50 queries, 10 docs), Pro ($29/mo), Team ($79/mo). Usage tracked in `usage_logs` + Redis counters.
