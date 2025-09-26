"""
Chat API — session CRUD + SSE message streaming.

All routes expect the gateway to inject:
  x-user-id      → authenticated user UUID
  x-workspace-id → workspace UUID (verified by gateway workspaceAccess middleware)

SSE message endpoint:
  POST /workspaces/{workspace_id}/chat/sessions/{session_id}/messages
  Streams: data: {"type":"token","content":"..."}\n\n
           data: {"type":"citations","citations":[...]}\n\n
           data: {"type":"done"}\n\n
"""
from __future__ import annotations

import json
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DbSession, CurrentUser
from app.rag.chain import rag_stream
from app.rag.retriever import RetrievedChunk
from app.rag.streaming import parse_citation_ids, strip_citations
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
    SendMessageRequest,
)
from app.services import chat_service
from app.services import usage_service
from app.utils.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/workspaces/{workspace_id}/chat", tags=["chat"])


# ---------------------------------------------------------------------------
# Helper — extract workspace_id from path OR x-workspace-id header
# ---------------------------------------------------------------------------

def _workspace_uuid(workspace_id: str) -> uuid.UUID:
    return uuid.UUID(workspace_id)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    workspace_id: str,
    body: ChatSessionCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    session = await chat_service.create_session(
        db=db,
        workspace_id=_workspace_uuid(workspace_id),
        user_id=current_user.id,
        title=body.title,
    )
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    workspace_id: str,
    db: DbSession,
    current_user: CurrentUser,
):
    return await chat_service.list_sessions(
        db=db,
        workspace_id=_workspace_uuid(workspace_id),
        user_id=current_user.id,
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    workspace_id: str,
    session_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    return await chat_service.get_session(
        db=db,
        session_id=session_id,
        workspace_id=_workspace_uuid(workspace_id),
    )


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    workspace_id: str,
    session_id: uuid.UUID,
    body: ChatSessionUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    session = await chat_service.update_session_title(
        db=db,
        session_id=session_id,
        workspace_id=_workspace_uuid(workspace_id),
        user_id=current_user.id,
        title=body.title,
    )
    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    workspace_id: str,
    session_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    await chat_service.delete_session(
        db=db,
        session_id=session_id,
        workspace_id=_workspace_uuid(workspace_id),
        user_id=current_user.id,
    )
    await db.commit()


# ---------------------------------------------------------------------------
# Message history
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryResponse)
async def get_history(
    workspace_id: str,
    session_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    ws_uuid = _workspace_uuid(workspace_id)
    session = await chat_service.get_session(db=db, session_id=session_id, workspace_id=ws_uuid)
    messages = await chat_service.get_session_history(
        db=db, session_id=session_id, workspace_id=ws_uuid
    )
    return {"session": session, "messages": messages}


@router.get("/sessions/{session_id}/messages/{message_id}/citations",
            response_model=ChatMessageResponse)
async def get_message_citations(
    workspace_id: str,
    session_id: uuid.UUID,
    message_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    return await chat_service.get_message_with_citations(
        db=db,
        message_id=message_id,
        workspace_id=_workspace_uuid(workspace_id),
    )


# ---------------------------------------------------------------------------
# SSE message endpoint
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/messages")
async def send_message(
    workspace_id: str,
    session_id: uuid.UUID,
    body: SendMessageRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Stream the RAG answer as SSE.
    Saves user message immediately; saves assistant message + citations after stream completes.

    The generator function must close the DB session itself because FastAPI
    cannot do cleanup inside a StreamingResponse after the response has started.
    """
    ws_uuid = _workspace_uuid(workspace_id)

    # Verify session belongs to this workspace
    await chat_service.get_session(db=db, session_id=session_id, workspace_id=ws_uuid)

    # Enforce query quota before processing
    await usage_service.enforce_query_quota(db, ws_uuid)

    # Save user message
    await chat_service.save_user_message(
        db=db,
        session_id=session_id,
        workspace_id=ws_uuid,
        content=body.content,
    )
    await db.commit()

    # Fetch recent history for context (exclude the message we just saved)
    history_msgs = await chat_service.get_session_history(
        db=db, session_id=session_id, workspace_id=ws_uuid, limit=20
    )
    # Build history dicts (skip the last user message we just added — it's the current question)
    history = [
        {"role": m.role, "content": m.content}
        for m in history_msgs[:-1]  # last item is the user msg we just saved
    ]

    doc_ids = body.document_ids

    async def _stream() -> AsyncIterator[bytes]:
        full_text = ""
        all_chunks: list[RetrievedChunk] = []
        cited_chunks: list[RetrievedChunk] = []

        try:
            async for sse_line in rag_stream(
                db=db,
                workspace_id=ws_uuid,
                question=body.content,
                history=history,
                document_ids=doc_ids,
            ):
                yield sse_line.encode()

                # Parse tokens to reconstruct full text and collect chunks
                if sse_line.startswith("data: "):
                    try:
                        payload = json.loads(sse_line[6:])
                        if payload.get("type") == "token":
                            full_text += payload.get("content", "")
                        elif payload.get("type") == "citations":
                            raw_citations = payload.get("citations", [])
                            cited_chunks = [
                                RetrievedChunk(
                                    id=c["chunk_id"],
                                    document_id=c["document_id"],
                                    content=c["content"],
                                    page_number=c.get("page_number"),
                                    chunk_index=0,
                                    score=c.get("score", 0.0),
                                )
                                for c in raw_citations
                            ]
                    except (json.JSONDecodeError, KeyError):
                        pass

        finally:
            # Persist assistant message after stream ends (or on error)
            if full_text:
                try:
                    await chat_service.save_assistant_message(
                        db=db,
                        session_id=session_id,
                        workspace_id=ws_uuid,
                        content=full_text,
                        cited_chunks=cited_chunks,
                    )
                    # Log usage after successful response
                    await usage_service.track_query(
                        db, ws_uuid, current_user.id, tokens_used=len(full_text) // 4
                    )
                    await db.commit()
                except Exception:
                    await db.rollback()

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
