from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------

class ChatSessionCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=512)


class ChatSessionUpdate(BaseModel):
    title: str = Field(max_length=512)


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Message schemas
# ---------------------------------------------------------------------------

class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=32_000)
    # Optional: restrict retrieval to specific documents
    document_ids: list[uuid.UUID] | None = None


class CitationResponse(BaseModel):
    id: uuid.UUID
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content_snapshot: str
    page_number: int | None
    score: float | None

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    workspace_id: uuid.UUID
    role: str
    content: str
    token_count: int
    created_at: datetime
    citations: list[CitationResponse] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

class ChatHistoryResponse(BaseModel):
    session: ChatSessionResponse
    messages: list[ChatMessageResponse]
