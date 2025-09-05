import uuid
from datetime import datetime
from io import BytesIO
from typing import BinaryIO

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.workspace import WorkspaceMember
from app.schemas.document import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
)
from app.utils.exceptions import (
    DocumentNotFoundError,
    FileTooLargeError,
    ForbiddenError,
    UnsupportedFileTypeError,
)
from app.utils import storage


# ---------------------------------------------------------------------------
# Access helpers
# ---------------------------------------------------------------------------


async def _assert_workspace_access(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    min_role: str = "viewer",
) -> None:
    _ROLE_RANK = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.invite_status == "accepted",
        )
    )
    mem = result.scalar_one_or_none()
    if mem is None or _ROLE_RANK.get(mem.role, -1) < _ROLE_RANK.get(min_role, 0):
        raise ForbiddenError("Insufficient workspace permissions")


async def _get_document_or_404(
    db: AsyncSession,
    document_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise DocumentNotFoundError()
    return doc


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


async def upload_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    mime_type: str,
    file_obj: BinaryIO,
    file_size: int,
) -> Document:
    await _assert_workspace_access(db, workspace_id, user_id, min_role="member")

    if mime_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(mime_type)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(50)

    key = storage.generate_storage_key(str(workspace_id), filename)
    storage.upload_file(file_obj, key, mime_type)

    # Derive title from filename (strip extension)
    title = filename.rsplit(".", 1)[0] if "." in filename else filename

    doc = Document(
        workspace_id=workspace_id,
        uploaded_by=user_id,
        title=title,
        filename=filename,
        mime_type=mime_type,
        file_size=file_size,
        storage_key=key,
        source="upload",
        status="pending",
    )
    db.add(doc)
    await db.flush()
    return doc


# ---------------------------------------------------------------------------
# URL scrape (creates a pending document row; worker does the actual fetch)
# ---------------------------------------------------------------------------


async def create_url_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    url: str,
    title: str | None,
) -> Document:
    await _assert_workspace_access(db, workspace_id, user_id, min_role="member")

    doc_title = title or url.split("/")[-1] or url
    doc = Document(
        workspace_id=workspace_id,
        uploaded_by=user_id,
        title=doc_title,
        filename=url,
        mime_type="text/html",
        file_size=0,
        source="url_scrape",
        source_url=url,
        status="pending",
    )
    db.add(doc)
    await db.flush()
    return doc


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------


async def list_documents(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Document], int]:
    await _assert_workspace_access(db, workspace_id, user_id, min_role="viewer")

    total_result = await db.execute(
        select(func.count()).where(Document.workspace_id == workspace_id)
    )
    total = total_result.scalar_one()

    docs_result = await db.execute(
        select(Document)
        .where(Document.workspace_id == workspace_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return docs_result.scalars().all(), total


async def get_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Document:
    await _assert_workspace_access(db, workspace_id, user_id, min_role="viewer")
    return await _get_document_or_404(db, document_id, workspace_id)


async def get_document_status(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Document:
    await _assert_workspace_access(db, workspace_id, user_id, min_role="viewer")
    return await _get_document_or_404(db, document_id, workspace_id)


# ---------------------------------------------------------------------------
# Update / Delete / Reprocess
# ---------------------------------------------------------------------------


async def update_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
) -> Document:
    await _assert_workspace_access(db, workspace_id, user_id, min_role="member")
    doc = await _get_document_or_404(db, document_id, workspace_id)
    doc.title = title
    doc.updated_at = datetime.utcnow()
    await db.flush()
    return doc


async def delete_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    await _assert_workspace_access(db, workspace_id, user_id, min_role="member")
    doc = await _get_document_or_404(db, document_id, workspace_id)
    if doc.storage_key:
        storage.delete_file(doc.storage_key)
    await db.delete(doc)
    await db.flush()


async def mark_reprocess(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Document:
    """Reset status to pending so the Celery worker will re-ingest the document."""
    await _assert_workspace_access(db, workspace_id, user_id, min_role="member")
    doc = await _get_document_or_404(db, document_id, workspace_id)
    doc.status = "pending"
    doc.error_message = None
    doc.chunk_count = 0
    doc.updated_at = datetime.utcnow()
    await db.flush()
    return doc
