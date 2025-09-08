"""
Workspace-scoped retriever.
Embeds the query, runs pgvector similarity search, returns RetrievedChunk list.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.embeddings import embed_texts
from app.rag.vectorstore import similarity_search


@dataclass
class RetrievedChunk:
    id: str
    document_id: str
    content: str
    page_number: int | None
    chunk_index: int
    score: float


async def retrieve(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    query: str,
    top_k: int | None = None,
    score_threshold: float | None = None,
    document_ids: list[uuid.UUID] | None = None,
) -> list[RetrievedChunk]:
    """Embed query and return top-k similar chunks scoped to workspace."""
    embeddings = await embed_texts([query])
    query_embedding = embeddings[0]

    raw = await similarity_search(
        db=db,
        workspace_id=workspace_id,
        query_embedding=query_embedding,
        top_k=top_k,
        score_threshold=score_threshold,
        document_ids=document_ids,
    )

    return [
        RetrievedChunk(
            id=str(r["id"]),
            document_id=str(r["document_id"]),
            content=r["content"],
            page_number=r.get("page_number"),
            chunk_index=r["chunk_index"],
            score=float(r["score"]),
        )
        for r in raw
    ]


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Format chunks into a context block with citation anchors."""
    parts = []
    for chunk in chunks:
        header = f"[SOURCE:{chunk.id}] (doc:{chunk.document_id}, page:{chunk.page_number}, score:{chunk.score:.3f})"
        parts.append(f"{header}\n{chunk.content}")
    return "\n\n---\n\n".join(parts)
