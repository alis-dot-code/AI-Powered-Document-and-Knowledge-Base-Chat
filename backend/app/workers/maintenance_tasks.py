"""
Maintenance Celery tasks.

Schedule via Celery Beat (add to celery_app.conf.beat_schedule):
  - cleanup_stale_documents: every 15 minutes
  - retry_failed_documents:  every 30 minutes
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.maintenance_tasks.cleanup_stale_documents",
    queue="documents",
)
def cleanup_stale_documents() -> dict:
    """
    Reset documents stuck in 'processing' for more than 30 minutes back to
    'failed' so they can be requeued. Guards against worker crashes.
    """
    return asyncio.run(_cleanup_stale())


async def _cleanup_stale() -> dict:
    from app.database import AsyncSessionLocal
    from app.models.document import Document

    cutoff = datetime.utcnow() - timedelta(minutes=30)
    updated = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(
                Document.status == "processing",
                Document.updated_at < cutoff,
            )
        )
        stale = result.scalars().all()
        for doc in stale:
            doc.status = "failed"
            doc.error_message = "Processing timed out — please reprocess."
            doc.updated_at = datetime.utcnow()
            updated += 1
        if updated:
            await db.commit()

    logger.info("cleanup_stale_documents: reset %d stale documents", updated)
    return {"reset": updated}


@celery_app.task(
    name="app.workers.maintenance_tasks.retry_failed_documents",
    queue="documents",
)
def retry_failed_documents(max_age_hours: int = 24, limit: int = 50) -> dict:
    """
    Re-queue failed documents that are younger than max_age_hours.
    Only retries documents without a permanent error (e.g. unsupported type).
    """
    return asyncio.run(_retry_failed(max_age_hours, limit))


async def _retry_failed(max_age_hours: int, limit: int) -> dict:
    from app.database import AsyncSessionLocal
    from app.models.document import Document
    from app.workers.document_tasks import process_document

    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    queued = 0

    # Permanent errors we don't retry
    SKIP_ERRORS = ("Unsupported file type", "File exceeds maximum size")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(
                Document.status == "failed",
                Document.updated_at >= cutoff,
            ).limit(limit)
        )
        docs = result.scalars().all()

        for doc in docs:
            err = doc.error_message or ""
            if any(skip in err for skip in SKIP_ERRORS):
                continue
            doc.status = "pending"
            doc.error_message = None
            doc.updated_at = datetime.utcnow()
            queued += 1

        if queued:
            await db.commit()
            # Re-fetch to get IDs after commit then dispatch tasks
            result2 = await db.execute(
                select(Document).where(
                    Document.status == "pending",
                    Document.updated_at >= datetime.utcnow() - timedelta(seconds=10),
                )
            )
            for doc in result2.scalars().all():
                process_document.delay(str(doc.id))

    logger.info("retry_failed_documents: queued %d documents for reprocessing", queued)
    return {"queued": queued}
