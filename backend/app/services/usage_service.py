"""
Usage tracking and quota enforcement.

Thin wrapper around billing_service usage functions, providing a dedicated
service module as specified in the plan. Also adds convenience helpers
for inline usage logging from chat and document endpoints.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing_service import (
    check_document_quota,
    check_query_quota,
    get_usage_stats,
    log_usage,
)


async def track_query(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID | None,
    tokens_used: int = 0,
) -> None:
    """Log a query usage event."""
    await log_usage(db, workspace_id, user_id, "query", tokens_used)


async def track_document_upload(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID | None,
) -> None:
    """Log a document upload event."""
    await log_usage(db, workspace_id, user_id, "document_upload", 0)


async def track_url_scrape(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID | None,
) -> None:
    """Log a URL scrape event."""
    await log_usage(db, workspace_id, user_id, "url_scrape", 0)


async def enforce_query_quota(
    db: AsyncSession, workspace_id: uuid.UUID
) -> None:
    """Raise QuotaExceededError if query limit reached."""
    await check_query_quota(db, workspace_id)


async def enforce_document_quota(
    db: AsyncSession, workspace_id: uuid.UUID
) -> None:
    """Raise QuotaExceededError if document limit reached."""
    await check_document_quota(db, workspace_id)
