"""
pgvector bulk-insert and similarity search helpers.
Uses raw SQL for performance — SQLAlchemy ORM would cast Vector columns awkwardly.
"""
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


async def bulk_insert_chunks(
    db: AsyncSession,
    document_id: uuid.UUID,
    workspace_id: uuid.UUID,
    chunks: list[dict],  # {content, chunk_index, page_number, embedding: list[float]}
) -> None:
    """
    Insert chunks with embeddings in a single COPY-style executemany.
    chunks: list of dicts with keys: content, chunk_index, page_number, embedding
    """
    now = datetime.utcnow()
    rows = [
        {
            "id": str(uuid.uuid4()),
            "document_id": str(document_id),
            "workspace_id": str(workspace_id),
            "content": c["content"],
            "chunk_index": c["chunk_index"],
            "page_number": c.get("page_number"),
            "embedding": str(c["embedding"]),  # pgvector accepts '[1.0, 2.0, ...]' literal
            "created_at": now,
        }
        for c in chunks
    ]
    await db.execute(
        text(
            """
            INSERT INTO document_chunks
                (id, document_id, workspace_id, content, chunk_index, page_number, embedding, created_at)
            VALUES
                (:id::uuid, :document_id::uuid, :workspace_id::uuid,
                 :content, :chunk_index, :page_number, :embedding::vector, :created_at)
            """
        ),
        rows,
    )


async def similarity_search(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    query_embedding: list[float],
    top_k: int | None = None,
    score_threshold: float | None = None,
    document_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """
    Cosine similarity search scoped to a workspace.
    Returns list of {id, document_id, content, page_number, chunk_index, score}.
    """
    k = top_k or settings.rag_top_k
    threshold = score_threshold if score_threshold is not None else settings.rag_score_threshold
    embedding_literal = str(query_embedding)

    doc_filter = ""
    params: dict = {
        "workspace_id": str(workspace_id),
        "embedding": embedding_literal,
        "threshold": threshold,
        "k": k,
    }

    if document_ids:
        doc_filter = "AND dc.document_id = ANY(:doc_ids::uuid[])"
        params["doc_ids"] = [str(d) for d in document_ids]

    sql = text(
        f"""
        SELECT
            dc.id,
            dc.document_id,
            dc.content,
            dc.page_number,
            dc.chunk_index,
            1 - (dc.embedding <=> :embedding::vector) AS score
        FROM document_chunks dc
        WHERE dc.workspace_id = :workspace_id::uuid
          {doc_filter}
          AND 1 - (dc.embedding <=> :embedding::vector) >= :threshold
        ORDER BY dc.embedding <=> :embedding::vector
        LIMIT :k
        """
    )
    result = await db.execute(sql, params)
    rows = result.mappings().all()
    return [dict(r) for r in rows]
