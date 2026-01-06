# DocMind — Deployment Guide

## Prerequisites

- Docker + Docker Compose v2
- OpenAI API key
- AWS S3 bucket (or Cloudinary account)
- Stripe account with products/prices created

## Quick Start (Production)

### 1. Clone and configure

```bash
git clone https://github.com/yourorg/docmind.git
cd docmind
cp .env.example .env
# Edit .env with your real values
```

### 2. Required `.env` values

```
DATABASE_URL=postgresql+asyncpg://docmind:<pass>@postgres:5432/docmind
REDIS_URL=redis://:<pass>@redis:6379/0
JWT_SECRET_KEY=<64+ char random string>
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=your-bucket-name
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_TEAM=price_...
FRONTEND_URL=https://yourdomain.com
VITE_API_URL=https://api.yourdomain.com
```

### 3. Build and start

```bash
docker compose up -d --build
```

### 4. Seed demo data (optional)

```bash
docker compose exec backend python ../scripts/seed.py
```

### 5. Create superadmin

```bash
docker compose exec backend python ../scripts/create_superuser.py admin@example.com Password1!
```

---

## Development

```bash
cp .env.example .env
# Only OPENAI_API_KEY and storage keys are required for local dev

docker compose -f docker-compose.dev.yml up -d

# Frontend hot reload runs at http://localhost:5173
# Gateway at http://localhost:3000
# Backend docs at http://localhost:8000/docs
```

---

## Stripe Webhook Setup

1. Install Stripe CLI: `stripe login`
2. Forward events in dev:
   ```bash
   stripe listen --forward-to localhost:3000/api/v1/billing/webhook/stripe
   ```
3. In production, configure webhook URL in Stripe dashboard:
   `https://api.yourdomain.com/api/v1/billing/webhook/stripe`
4. Subscribe to events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`

---

## Health Checks

| Service | URL |
|---------|-----|
| Frontend | `GET /health` → `{"status":"ok"}` |
| Gateway | `GET /health` → `{"status":"ok","service":"gateway"}` |
| Backend | `GET /health` → `{"status":"ok","environment":"..."}` |

---

## Embeddable Widget

After generating an API key in the workspace settings:

```html
<script src="https://cdn.yourdomain.com/widget/docmind-widget.iife.js"></script>
<script>
  DocMindWidget.init({
    apiKey: 'dm_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    gatewayUrl: 'https://api.yourdomain.com',
  })
</script>
```

Build the widget bundle:
```bash
cd widget
npm install
npm run build
# Output: widget/dist/docmind-widget.iife.js
```
