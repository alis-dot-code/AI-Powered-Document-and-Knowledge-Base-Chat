from fastapi import APIRouter

from app.api.v1 import auth, workspaces, documents, chat, billing, widget, admin

# ---------------------------------------------------------------------------
# Aggregate all v1 sub-routers here.
# Add each new router below as prompts are implemented.
# ---------------------------------------------------------------------------

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth.router)
v1_router.include_router(workspaces.router)
v1_router.include_router(documents.router)
v1_router.include_router(chat.router)
v1_router.include_router(billing.router)
v1_router.include_router(widget.router)
v1_router.include_router(widget.api_keys_router)
v1_router.include_router(admin.router)
