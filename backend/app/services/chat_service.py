"""
Chat service — session CRUD and message persistence.
The actual RAG streaming lives in app.rag.chain; this service handles DB state.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, ChatSession, Citation
from app.rag.retriever import RetrievedChunk
from app.utils.exceptions import ForbiddenError, NotFoundError


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

async def create_session(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str = "New Chat",
) -> ChatSession:
    session = ChatSession(
        workspace_id=workspace_id,
        user_id=user_id,
        title=title,
    )
    db.add(session)
    await db.flush()
    return session


async def get_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.workspace_id == workspace_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("Chat session")
    return session


async def list_sessions(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.workspace_id == workspace_id,
            ChatSession.user_id == user_id,
        )
        .order_by(ChatSession.updated_at.desc())
    )
    return list(result.scalars().all())


async def delete_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    session = await get_session(db, session_id, workspace_id)
    if session.user_id != user_id:
        raise ForbiddenError("You do not own this chat session")
    await db.delete(session)
    await db.flush()


async def update_session_title(
    db: AsyncSession,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
) -> ChatSession:
    session = await get_session(db, session_id, workspace_id)
    if session.user_id != user_id:
        raise ForbiddenError("You do not own this chat session")
    session.title = title
    session.updated_at = datetime.utcnow()
    await db.flush()
    return session


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------

async def save_user_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
    content: str,
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session_id,
        workspace_id=workspace_id,
        role="user",
        content=content,
        token_count=len(content.split()),  # rough approximation
    )
    db.add(msg)
    await db.flush()
    return msg


async def save_assistant_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
    content: str,
    cited_chunks: list[RetrievedChunk],
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session_id,
        workspace_id=workspace_id,
        role="assistant",
        content=content,
        token_count=len(content.split()),
    )
    db.add(msg)
    await db.flush()

    # Persist citations
    for chunk in cited_chunks:
        citation = Citation(
            message_id=msg.id,
            chunk_id=uuid.UUID(chunk.id),
            document_id=uuid.UUID(chunk.document_id),
            content_snapshot=chunk.content[:1000],
            page_number=chunk.page_number,
            score=chunk.score,
        )
        db.add(citation)

    await db.flush()

    # Touch session updated_at
    await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    return msg


async def get_session_history(
    db: AsyncSession,
    session_id: uuid.UUID,
    workspace_id: uuid.UUID,
    limit: int = 20,
) -> list[ChatMessage]:
    """Return recent messages with citations loaded, oldest first."""
    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.workspace_id == workspace_id,
        )
        .options(selectinload(ChatMessage.citations))
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    return list(reversed(messages))  # return oldest-first


async def get_message_with_citations(
    db: AsyncSession,
    message_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> ChatMessage:
    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.id == message_id,
            ChatMessage.workspace_id == workspace_id,
        )
        .options(selectinload(ChatMessage.citations))
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise NotFoundError("Message")
    return msg
