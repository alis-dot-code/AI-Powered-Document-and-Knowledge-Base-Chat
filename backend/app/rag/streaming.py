"""
SSE streaming helpers for RAG chain responses.
Yields Server-Sent Events in the format the frontend's useSSE hook expects.

Event types:
  data: {"type": "token",    "content": "..."}
  data: {"type": "citations","citations": [...]}
  data: {"type": "done"}
  data: {"type": "error",   "message": "..."}
"""
from __future__ import annotations

import json
import re
from typing import AsyncIterator

from app.rag.retriever import RetrievedChunk


# Regex to strip [SOURCE:uuid] markers from the final text (frontend re-adds them)
_SOURCE_RE = re.compile(r"\[SOURCE:[^\]]+\]")


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def strip_citations(text: str) -> str:
    return _SOURCE_RE.sub("", text).strip()


def extract_cited_ids(text: str) -> list[str]:
    return _SOURCE_RE.findall(text)  # returns full '[SOURCE:uuid]' strings; caller strips


def parse_citation_ids(text: str) -> list[str]:
    """Return just the chunk_id values referenced in the text."""
    return [m[len("[SOURCE:") : -1] for m in _SOURCE_RE.findall(text)]


async def stream_tokens(
    token_stream: AsyncIterator[str],
    chunks: list[RetrievedChunk],
) -> AsyncIterator[str]:
    """
    Consume a raw LLM token stream, forward tokens as SSE, then emit citations event.

    The full assistant text is accumulated to determine which source chunks were
    actually cited; only those chunks are forwarded as citations.
    """
    full_text = ""

    try:
        async for token in token_stream:
            full_text += token
            # Forward tokens without the citation markers — frontend renders them separately
            clean = strip_citations(token)
            if clean:
                yield _sse({"type": "token", "content": clean})

        # Build citations from chunks that were actually referenced
        cited_ids = set(parse_citation_ids(full_text))
        chunk_map = {c.id: c for c in chunks}
        citations = [
            {
                "chunk_id": c.id,
                "document_id": c.document_id,
                "content": c.content[:300],
                "page_number": c.page_number,
                "score": round(c.score, 4),
            }
            for cid in cited_ids
            if (c := chunk_map.get(cid))
        ]
        yield _sse({"type": "citations", "citations": citations})
        yield _sse({"type": "done"})

    except Exception as exc:  # noqa: BLE001
        yield _sse({"type": "error", "message": str(exc)})
