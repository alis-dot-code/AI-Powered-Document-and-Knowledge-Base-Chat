"""
Prompt templates for the RAG chain.
Citation format: [DOC_ID:chunk_index] inline markers that the frontend renders.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_PROMPT = """You are a helpful assistant with access to a knowledge base.
Answer the user's question using ONLY the provided context chunks.
If the context doesn't contain enough information, say so clearly — do not fabricate.

When you use information from a chunk, cite it inline using the marker format: [SOURCE:{chunk_id}]
You MUST cite every factual claim. Multiple citations per sentence are fine: [SOURCE:abc] [SOURCE:def]

Context chunks:
{context}

Current date: {current_date}"""

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)

CONDENSE_QUESTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given the chat history and a follow-up question, rewrite the question "
            "to be a standalone question that captures all necessary context. "
            "Output ONLY the rewritten question, nothing else.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "Follow-up question: {question}"),
    ]
)
