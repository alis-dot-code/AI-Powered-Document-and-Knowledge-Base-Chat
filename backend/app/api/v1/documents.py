import uuid

from fastapi import APIRouter, File, Form, Query, UploadFile

from app.dependencies import CurrentUser, DbSession
from app.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
    ScrapeUrlRequest,
    UpdateDocumentRequest,
)
from app.services import document_service

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["documents"])


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    workspace_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = ...,
    db: DbSession = ...,
):
    contents = await file.read()
    file_size = len(contents)
    import io
    doc = await document_service.upload_document(
        db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        filename=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream",
        file_obj=io.BytesIO(contents),
        file_size=file_size,
    )

    # Dispatch Celery task (imported lazily to avoid hard dep before workers are set up)
    try:
        from app.workers.document_tasks import process_document  # noqa: F401
        process_document.delay(str(doc.id))
    except ImportError:
        pass  # Celery not yet wired — task will run when worker starts

    return doc


# ---------------------------------------------------------------------------
# URL scrape
# ---------------------------------------------------------------------------


@router.post("/scrape", response_model=DocumentResponse, status_code=201)
async def scrape_url(
    workspace_id: uuid.UUID,
    body: ScrapeUrlRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    doc = await document_service.create_url_document(
        db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        url=body.url,
        title=body.title,
    )

    try:
        from app.workers.document_tasks import process_document  # noqa: F401
        process_document.delay(str(doc.id))
    except ImportError:
        pass

    return doc


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    docs, _ = await document_service.list_documents(
        db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )
    return docs


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    return await document_service.get_document(
        db,
        workspace_id=workspace_id,
        document_id=document_id,
        user_id=current_user.id,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    return await document_service.get_document_status(
        db,
        workspace_id=workspace_id,
        document_id=document_id,
        user_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# Update / Delete / Reprocess
# ---------------------------------------------------------------------------


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    body: UpdateDocumentRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    return await document_service.update_document(
        db,
        workspace_id=workspace_id,
        document_id=document_id,
        user_id=current_user.id,
        title=body.title or "",
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    await document_service.delete_document(
        db,
        workspace_id=workspace_id,
        document_id=document_id,
        user_id=current_user.id,
    )


@router.post("/{document_id}/reprocess", response_model=DocumentStatusResponse)
async def reprocess_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    doc = await document_service.mark_reprocess(
        db,
        workspace_id=workspace_id,
        document_id=document_id,
        user_id=current_user.id,
    )

    try:
        from app.workers.document_tasks import process_document  # noqa: F401
        process_document.delay(str(doc.id))
    except ImportError:
        pass

    return doc
