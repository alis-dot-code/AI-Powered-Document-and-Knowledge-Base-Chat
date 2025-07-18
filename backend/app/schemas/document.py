import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

DocumentStatus = Literal["pending", "processing", "completed", "failed"]
DocumentSource = Literal["upload", "url_scrape"]

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/msword",  # doc
    "text/plain",
    "text/csv",
    "application/csv",
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ScrapeUrlRequest(BaseModel):
    url: str = Field(..., min_length=1)
    title: str | None = Field(None, max_length=512)


class UpdateDocumentRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=512)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class DocumentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    uploaded_by: uuid.UUID | None
    title: str
    filename: str
    mime_type: str
    file_size: int
    source: DocumentSource
    source_url: str | None
    status: DocumentStatus
    error_message: str | None
    chunk_count: int
    page_count: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: DocumentStatus
    chunk_count: int
    error_message: str | None

    model_config = {"from_attributes": True}
