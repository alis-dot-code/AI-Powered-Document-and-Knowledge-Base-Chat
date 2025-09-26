"""
RAG chain: retrieve → build prompt → stream GPT-4o response.

Usage:
    async for sse_chunk in rag_stream(db, workspace_id, question, history):
        yield sse_chunk
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.rag.prompts import RAG_PROMPT, CONDENSE_QUESTION_PROMPT
from app.rag.retriever import RetrievedChunk, retrieve, format_context
from app.rag.streaming import stream_tokens


def _build_history(messages: list[dict]) -> list[BaseMessage]:
    """Convert [{role, content}] dicts to LangChain message objects."""
    result: list[BaseMessage] = []
    for m in messages:
        if m["role"] == "user":
            result.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            result.append(AIMessage(content=m["content"]))
    return result


def _get_llm(streaming: bool = True) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0,
        streaming=streaming,
    )


async def _condense_question(
    question: str,
    history: list[BaseMessage],
) -> str:
    """If there's history, rewrite question as standalone. Otherwise return as-is."""
    if not history:
        return question

    llm = _get_llm(streaming=False)
    chain = CONDENSE_QUESTION_PROMPT | llm
    result = await chain.ainvoke({"question": question, "chat_history": history})
    return result.content  # type: ignore[return-value]


async def rag_stream(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    question: str,
    history: list[dict] | None = None,
    document_ids: list[uuid.UUID] | None = None,
) -> AsyncIterator[str]:
    """
    Full RAG pipeline — yields SSE strings.

    1. Condense follow-up question if chat history present.
    2. Retrieve top-k chunks from pgvector.
    3. Build prompt with context + history.
    4. Stream GPT-4o response as SSE tokens.
    5. Emit citations event.
    6. Emit done event.
    """
    lc_history = _build_history(history or [])

    # Step 1: condense
    standalone = await _condense_question(question, lc_history)

    # Step 2: retrieve
    chunks: list[RetrievedChunk] = await retrieve(
        db=db,
        workspace_id=workspace_id,
        query=standalone,
        document_ids=document_ids,
    )

    context = format_context(chunks) if chunks else "No relevant documents found."

    # Step 3: build prompt + stream
    llm = _get_llm(streaming=True)
    chain = RAG_PROMPT | llm

    async def _token_gen() -> AsyncIterator[str]:
        async for event in chain.astream(
            {
                "context": context,
                "chat_history": lc_history,
                "question": question,
                "current_date": date.today().isoformat(),
            }
        ):
            if hasattr(event, "content") and event.content:
                yield event.content

    async for sse in stream_tokens(_token_gen(), chunks):
        yield sse


async def rag_invoke(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    question: str,
    history: list[dict] | None = None,
    document_ids: list[uuid.UUID] | None = None,
) -> tuple[str, list[RetrievedChunk]]:
    """
    Non-streaming variant — returns (answer_text, cited_chunks).
    Used for testing and background tasks.
    """
    lc_history = _build_history(history or [])
    standalone = await _condense_question(question, lc_history)

    chunks = await retrieve(
        db=db,
        workspace_id=workspace_id,
        query=standalone,
        document_ids=document_ids,
    )
    context = format_context(chunks) if chunks else "No relevant documents found."

    llm = _get_llm(streaming=False)
    chain = RAG_PROMPT | llm
    result = await chain.ainvoke(
        {
            "context": context,
            "chat_history": lc_history,
            "question": question,
            "current_date": date.today().isoformat(),
        }
    )
    return result.content, chunks  # type: ignore[return-value]
