"""
Splits parsed document text into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter, then attaches page-number metadata.
"""
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


@dataclass
class Chunk:
    content: str
    chunk_index: int
    page_number: int | None


def chunk_document(pages: list[dict]) -> list[Chunk]:
    """
    pages: list of {"page_number": int, "text": str}
    Returns ordered Chunk list.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []
    idx = 0

    for page in pages:
        text = page.get("text", "").strip()
        if not text:
            continue
        page_num = page.get("page_number")
        splits = splitter.split_text(text)
        for split in splits:
            if split.strip():
                chunks.append(Chunk(content=split.strip(), chunk_index=idx, page_number=page_num))
                idx += 1

    return chunks
