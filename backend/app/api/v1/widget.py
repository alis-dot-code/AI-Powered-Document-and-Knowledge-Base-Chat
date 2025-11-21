"""
Widget API — API-key authenticated endpoints for the embeddable chat widget.

Auth: Bearer <api_key> in Authorization header (no JWT).
CORS: gateway enforces origin restrictions; backend trusts gateway.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import AsyncIterator

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models.api_key import ApiKey
from app.models.chat import ChatSession
from app.rag.chain import rag_stream
from app.rag.retriever import RetrievedChunk
from app.rag.streaming import parse_citation_ids
from app.schemas.chat import SendMessageRequest, ChatSessionCreate, ChatSessionResponse
from app.services import chat_service
from app.utils.exceptions import UnauthorizedError, NotFoundError
from app.utils.security import verify_api_key

router = APIRouter(prefix="/widget", tags=["widget"])


# ---------------------------------------------------------------------------
# API key dependency
# ---------------------------------------------------------------------------

async def _get_api_key(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("API key required")
    raw_key = authorization.removeprefix("Bearer ").strip()

    # Key prefix is first 12 chars — use for fast lookup
    prefix = raw_key[:12]
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()
    if not api_key or not verify_api_key(raw_key, api_key.key_hash):
        raise UnauthorizedError("Invalid API key")

    # Update last_used_at (fire-and-forget style)
    await db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key.id)
        .values(last_used_at=datetime.utcnow())
    )
    await db.flush()
    return api_key


ValidApiKey = Depends(_get_api_key)


# ---------------------------------------------------------------------------
# Widget config — returns workspace name, allowed behaviour flags
# ---------------------------------------------------------------------------

@router.get("/config")
async def get_widget_config(
    api_key: ApiKey = ValidApiKey,
    db: AsyncSession = Depends(get_db),
):
    from app.models.workspace import Workspace  # noqa: PLC0415
    result = await db.execute(
        select(Workspace).where(Workspace.id == api_key.workspace_id)
    )
    ws = result.scalar_one_or_none()
    return {
        "workspace_id": str(api_key.workspace_id),
        "workspace_name": ws.name if ws else "DocMind",
        "key_name": api_key.name,
    }


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_widget_session(
    api_key: ApiKey = ValidApiKey,
    db: AsyncSession = Depends(get_db),
):
    session = await chat_service.create_session(
        db=db,
        workspace_id=api_key.workspace_id,
        user_id=None,
        title="Widget Chat",
    )
    await db.commit()
    await db.refresh(session)
    return session


# ---------------------------------------------------------------------------
# Chat — SSE stream
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/chat")
async def widget_chat(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    api_key: ApiKey = ValidApiKey,
    db: AsyncSession = Depends(get_db),
):
    ws_uuid = api_key.workspace_id

    # Verify session belongs to this workspace
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.workspace_id == ws_uuid,
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundError("Session")

    # Save user message
    await chat_service.save_user_message(
        db=db, session_id=session_id, workspace_id=ws_uuid, content=body.content
    )
    await db.commit()

    history_msgs = await chat_service.get_session_history(
        db=db, session_id=session_id, workspace_id=ws_uuid, limit=20
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in history_msgs[:-1]
    ]

    async def _stream() -> AsyncIterator[bytes]:
        full_text = ""
        cited_chunks: list[RetrievedChunk] = []

        try:
            async for sse_line in rag_stream(
                db=db,
                workspace_id=ws_uuid,
                question=body.content,
                history=history,
                document_ids=body.document_ids,
            ):
                yield sse_line.encode()

                if sse_line.startswith("data: "):
                    try:
                        payload = json.loads(sse_line[6:])
                        if payload.get("type") == "token":
                            full_text += payload.get("content", "")
                        elif payload.get("type") == "citations":
                            cited_chunks = [
                                RetrievedChunk(
                                    id=c["chunk_id"],
                                    document_id=c["document_id"],
                                    content=c["content"],
                                    page_number=c.get("page_number"),
                                    chunk_index=0,
                                    score=c.get("score", 0.0),
                                )
                                for c in payload.get("citations", [])
                            ]
                    except (json.JSONDecodeError, KeyError):
                        pass
        finally:
            if full_text:
                try:
                    await chat_service.save_assistant_message(
                        db=db,
                        session_id=session_id,
                        workspace_id=ws_uuid,
                        content=full_text,
                        cited_chunks=cited_chunks,
                    )
                    await db.commit()
                except Exception:
                    await db.rollback()

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# API Key CRUD — requires JWT auth (normal user), not API key auth
# ---------------------------------------------------------------------------

from app.dependencies import CurrentUser, DbSession  # noqa: E402

api_keys_router = APIRouter(prefix="/workspaces/{workspace_id}/api-keys", tags=["api-keys"])


@api_keys_router.post("", status_code=201)
async def create_api_key(
    workspace_id: uuid.UUID,
    name: str,
    db: DbSession,
    current_user: CurrentUser,
):
    from app.utils.security import generate_api_key

    raw, prefix, hashed = generate_api_key()
    key = ApiKey(
        workspace_id=workspace_id,
        created_by=current_user.id,
        name=name,
        key_prefix=prefix,
        key_hash=hashed,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    return {
        "id": str(key.id),
        "name": key.name,
        "key": raw,  # shown only once
        "key_prefix": key.key_prefix,
        "created_at": key.created_at.isoformat(),
    }


@api_keys_router.get("")
async def list_api_keys(
    workspace_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.workspace_id == workspace_id, ApiKey.is_active == True
        )
    )
    keys = result.scalars().all()
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat(),
        }
        for k in keys
    ]


@api_keys_router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    workspace_id: uuid.UUID,
    key_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id, ApiKey.workspace_id == workspace_id
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise NotFoundError("API key")
    key.is_active = False
    await db.commit()
