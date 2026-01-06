# DocMind API Reference

Base URL: `http://localhost:3000/api/v1` (via gateway)

All authenticated endpoints require either:
- httpOnly cookie `access_token` (web app), or
- `Authorization: Bearer <jwt>` header

---

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Register new user |
| POST | `/auth/login` | — | Login, sets httpOnly cookie |
| POST | `/auth/logout` | ✓ | Clear session |
| POST | `/auth/refresh` | — | Refresh access token |
| GET | `/auth/me` | ✓ | Get current user |
| PATCH | `/auth/me` | ✓ | Update profile |
| POST | `/auth/forgot-password` | — | Send reset email |
| POST | `/auth/reset-password` | — | Reset password |

## Workspaces

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workspaces` | Create workspace |
| GET | `/workspaces` | List user's workspaces |
| GET | `/workspaces/:id` | Get workspace |
| PATCH | `/workspaces/:id` | Update workspace |
| DELETE | `/workspaces/:id` | Delete workspace |
| POST | `/workspaces/:id/invite` | Invite member by email |
| GET | `/workspaces/:id/members` | List members |
| PATCH | `/workspaces/:id/members/:userId` | Change member role |
| DELETE | `/workspaces/:id/members/:userId` | Remove member |
| POST | `/workspaces/:id/accept-invite` | Accept invite token |

## Documents

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workspaces/:id/documents` | Upload file (multipart) |
| POST | `/workspaces/:id/documents/scrape` | Scrape URL |
| GET | `/workspaces/:id/documents` | List documents |
| GET | `/workspaces/:id/documents/:docId` | Get document |
| GET | `/workspaces/:id/documents/:docId/status` | Processing status |
| POST | `/workspaces/:id/documents/:docId/reprocess` | Reprocess |
| DELETE | `/workspaces/:id/documents/:docId` | Delete |

**Supported file types:** PDF, DOCX, TXT, CSV, MD

## Chat

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workspaces/:id/chat/sessions` | Create session |
| GET | `/workspaces/:id/chat/sessions` | List sessions |
| GET | `/workspaces/:id/chat/sessions/:sid` | Get session |
| PATCH | `/workspaces/:id/chat/sessions/:sid` | Rename session |
| DELETE | `/workspaces/:id/chat/sessions/:sid` | Delete session |
| GET | `/workspaces/:id/chat/sessions/:sid/messages` | Get history |
| **POST** | `/workspaces/:id/chat/sessions/:sid/messages` | **Send message (SSE)** |

### SSE Stream Format
```
data: {"type": "token", "content": "Hello"}
data: {"type": "citations", "citations": [{...}]}
data: {"type": "done"}
data: {"type": "error", "message": "..."}
```

## Billing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/billing/plans` | List plans (public) |
| GET | `/billing/workspaces/:id/subscription` | Get subscription |
| POST | `/billing/workspaces/:id/checkout` | Create Stripe checkout |
| POST | `/billing/workspaces/:id/portal` | Open Stripe portal |
| GET | `/billing/workspaces/:id/usage` | Usage stats |
| POST | `/billing/webhook/stripe` | Stripe webhook (no auth) |

## API Keys (Widget)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workspaces/:id/api-keys` | Create API key |
| GET | `/workspaces/:id/api-keys` | List API keys |
| DELETE | `/workspaces/:id/api-keys/:keyId` | Revoke API key |

## Widget (API key auth)

Base URL: `/api/v1/widget`  
Auth: `Authorization: Bearer dm_live_<key>`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/widget/config` | Widget config |
| POST | `/widget/sessions` | Create session |
| POST | `/widget/sessions/:sid/chat` | Chat (SSE) |

## Admin (superadmin only)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/stats` | System stats |
| GET | `/admin/users` | List all users |
| PATCH | `/admin/users/:id` | Update user |
| GET | `/admin/workspaces` | List all workspaces |
