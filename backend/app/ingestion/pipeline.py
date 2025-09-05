"""
Ingestion pipeline: parse -> chunk -> embed -> store.
Called synchronously from Celery workers (uses asyncio.run internally).
"""
import asyncio
import logging
import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.ingestion import chunker
from app.ingestion.parsers import get_parser
from app.models.document import Document, DocumentChunk
from app.rag import embeddings as emb
from app.rag import vectorstore
from app.utils.storage import download_file_bytes

logger = logging.getLogger(__name__)


async def _run(document_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if doc is None:
            logger.error("Document %s not found", document_id)
            return

        doc.status = "processing"
        doc.updated_at = datetime.utcnow()
        await db.commit()

        try:
            await _process(db, doc)
        except Exception as exc:
            logger.exception("Pipeline failed for document %s", document_id)
            async with AsyncSessionLocal() as err_db:
                r2 = await err_db.execute(select(Document).where(Document.id == document_id))
                d2 = r2.scalar_one_or_none()
                if d2:
                    d2.status = "failed"
                    d2.error_message = str(exc)[:1000]
                    d2.updated_at = datetime.utcnow()
                    await err_db.commit()
            raise


async def _process(db: AsyncSession, doc: Document) -> None:
    # 1. Fetch + parse
    if doc.source == "url_scrape":
        from app.ingestion.parsers.url_scraper import scrape_url
        parsed = scrape_url(doc.source_url or "")
    else:
        file_bytes = download_file_bytes(doc.storage_key)
        mime = doc.mime_type
        parser = get_parser(mime)
        parsed = parser.parse(file_bytes)

    pages: list[dict] = []
    for p in parsed.pages:
        if isinstance(p, dict):
            pages.append(p)
        else:
            pages.append({"page_number": getattr(p, "page_number", 1), "text": p.text})

    # 3. Chunk
    chunks = chunker.chunk_document(pages)
    if not chunks:
        doc.status = "completed"
        doc.chunk_count = 0
        doc.page_count = getattr(parsed, "page_count", 1)
        doc.updated_at = datetime.utcnow()
        await db.commit()
        return

    # 4. Embed
    texts = [c.content for c in chunks]
    embedding_vectors = emb.embed_texts_sync(texts)

    # 5. Delete existing chunks (reprocess)
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))

    # 6. Bulk insert with vectors
    chunk_rows = [
        {
            "content": c.content,
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,
            "embedding": embedding_vectors[i],
        }
        for i, c in enumerate(chunks)
    ]
    await vectorstore.bulk_insert_chunks(db, doc.id, doc.workspace_id, chunk_rows)

    # 7. Finalize
    doc.status = "completed"
    doc.chunk_count = len(chunks)
    doc.page_count = getattr(parsed, "page_count", 1)
    doc.updated_at = datetime.utcnow()
    await db.commit()

    logger.info("Document %s: %d chunks, %d pages", doc.id, len(chunks), doc.page_count or 1)


def run_pipeline(document_id: str) -> None:
    """Entry point for Celery task."""
    asyncio.run(_run(uuid.UUID(document_id)))
