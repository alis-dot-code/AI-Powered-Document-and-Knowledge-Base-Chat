## Smart Document Chat & Knowledge Engine

Full-featured Retrieval-Augmented Generation (RAG) platform that lets teams turn documents and web content into an interactive, citation-aware chat assistant.

---

## Overview

- Purpose: Turn documents into a searchable knowledge layer and answer questions with source citations.
- Stack: React + Vite frontend, Node gateway for auth/routing, and a FastAPI backend powering RAG and ingestion.
- Use cases: internal knowledgebases, customer support assistants, research tools, and embeddable site chatbots.

---

## System Layout

Frontend → Gateway → Backend (RAG core)

- Storage: PostgreSQL with pgvector for embeddings
- Cache/Broker: Redis (caching, Celery broker)
- Background processing: Celery workers for document ingestion and maintenance

---

## Key Components

- Frontend: React 18 + TypeScript, Vite development server, embeddable widget bundle
- Gateway: Node/Express proxy that handles auth, throttling, and request routing
- Backend: FastAPI application implementing ingestion, embedding, retrieval, and streaming responses
- Worker: Celery workers for async ingestion and processing

---

## Highlights

- Document ingestion: Upload PDFs, Word docs, text files, CSVs, or index content from URLs.
- RAG-powered chat: Contextual answers with linked source citations from documents.
- Live streaming: Server-sent events (SSE) for incremental answer streaming.
- Multi-workspace support: Isolate knowledge bases and manage team roles.
- Embeddable widget: Drop-in chat widget for any website.
- Billing & usage: Stripe integration for subscription plans and usage tracking.

---

## Quickstart (Docker — recommended)

1. Clone the repo and create an environment file:

```bash
git clone https://github.com/your-org/folder.git
cd folder
cp .env.example .env
# Edit .env to add API keys and DB credentials
```

2. Start the stack for development:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

3. Apply DB migrations:

```bash
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

4. Open services:

- Frontend: http://localhost:5173
- Gateway: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

---

## Local Dev (without Docker)

- Backend:

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate    # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

- Celery worker:

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=debug
```

- Gateway:

```bash
cd gateway
npm install
npm run dev
```

- Frontend:

```bash
cd frontend
npm install
npm run dev
```

---

## Environment

See [.env.example](.env.example) for environment variable names and descriptions.

---

## Data model (high level)

- `users` — authentication and profiles
- `workspaces` — isolated knowledge contexts
- `documents` — raw uploaded files and indexed URLs
- `document_chunks` — text segments with `vector(1536)` embeddings
- `chat_sessions` / `chat_messages` — conversation history
- `citations` — mapping answers to source documents

---

## API docs

The backend exposes OpenAPI docs:

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Project Layout

Top-level folders:

- `frontend/` — React app and widget
- `gateway/` — Node gateway and proxy logic
- `backend/` — FastAPI service, ingestion, RAG code
- `widget/` — embeddable chat bundle
- `scripts/` — helper/seed scripts

---

## Licensing

This project is released under the MIT license.

---

If you'd like, I can further tailor the README tone (concise, marketing-focused, or technical) or add examples for deploying to production.
