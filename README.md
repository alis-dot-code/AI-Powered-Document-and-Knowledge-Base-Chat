# DocMind — AI-Powered Document & Knowledge Base Chat

A production-ready RAG (Retrieval-Augmented Generation) system for chatting with your documents using GPT-4o with source citations.

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Frontend  │────▶│  Node Gateway   │────▶│  FastAPI Backend │
│ React + TS  │     │ Auth + Routing  │     │  RAG + AI Core   │
└─────────────┘     └─────────────────┘     └────────┬─────────┘
                                                      │
                              ┌───────────────────────┼───────────────────────┐
                              │                       │                       │
                    ┌─────────▼──────┐    ┌──────────▼──────┐    ┌──────────▼──────┐
                    │   PostgreSQL   │    │     Redis        │    │  Celery Worker  │
                    │  + pgvector    │    │  Cache + Queue   │    │  Doc Processing │
                    └────────────────┘    └─────────────────┘    └─────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5173 (dev) / 80 (prod) | React 18 + TypeScript + Vite |
| Gateway | 3000 | Node.js + Express (auth, rate limiting, proxy) |
| Backend | 8000 | FastAPI + Python (RAG, document processing) |
| Worker | — | Celery worker (background doc ingestion) |
| PostgreSQL | 5432 | Database + pgvector for embeddings |
| Redis | 6379 | Cache + Celery broker |

## Features

- **Document Ingestion**: Upload PDF, DOCX, TXT, CSV or paste URLs
- **RAG Chat**: Ask questions, get answers with source citations
- **Streaming**: Real-time SSE streaming responses
- **Workspaces**: Multi-workspace with team roles (Owner/Editor/Viewer)
- **Embeddable Widget**: Embed as a chatbot on any website
- **Usage & Billing**: Stripe-powered subscription plans

## Quick Start (Development)

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### 1. Clone and configure

```bash
git clone https://github.com/your-org/docmind.git
cd docmind
cp .env.example .env
# Edit .env with your OpenAI API key, Stripe keys, etc.
```

### 2. Start with Docker Compose (dev)

```bash
docker-compose -f docker-compose.dev.yml up --build
```

### 3. Run database migrations

```bash
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

### 4. Access the app

- Frontend: http://localhost:5173
- Gateway API: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Backend ReDoc: http://localhost:8000/redoc

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Celery Worker

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=debug
```

### Gateway

```bash
cd gateway
npm install
npm run dev
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

See [.env.example](.env.example) for all required environment variables.

## Database Schema

Key tables:
- `users` — Authentication
- `workspaces` — Isolated knowledge bases
- `documents` — Uploaded files and URLs
- `document_chunks` — Text chunks with `vector(1536)` embeddings
- `chat_sessions` + `chat_messages` — Conversation history
- `citations` — Source references per answer
- `subscriptions` — Stripe billing

## API Documentation

The FastAPI backend auto-generates OpenAPI docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
DocMind/
├── frontend/       # React 18 + TypeScript (Vite)
├── gateway/        # Node.js + Express (API gateway + auth)
├── backend/        # FastAPI + Python (RAG core)
├── widget/         # Embeddable chat widget (IIFE bundle)
├── scripts/        # Seed scripts
├── docs/           # Architecture & API docs
├── docker-compose.yml
└── docker-compose.dev.yml
```

## Plans

| Plan | Price | Docs | Queries/mo |
|------|-------|------|------------|
| Free | $0 | 3 | 100 |
| Pro | $19/mo | Unlimited | 1,000 |
| Team | $49/mo | Unlimited | 10,000 |

## License

MIT
