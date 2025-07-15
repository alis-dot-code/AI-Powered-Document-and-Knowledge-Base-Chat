import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # title derived from filename on upload; can be updated
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    # original filename
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    # mime type e.g. application/pdf
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    # file size in bytes
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    # s3 key / cloudinary public_id
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # source: upload | url_scrape
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="upload")
    # original URL if scraped
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # processing status: pending | processing | completed | failed
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # number of chunks after processing
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # page count (PDFs)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")  # type: ignore[name-defined]  # noqa: F821
    uploader: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by])  # type: ignore[name-defined]  # noqa: F821
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title!r} status={self.status}>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # embedding stored as pgvector Vector(1536) — added via raw DDL in migration
    # mapped here as a plain column using Text to avoid hard pgvector dep in model layer
    # The actual vector type is enforced at the DB level
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow
    )

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} doc={self.document_id} idx={self.chunk_index}>"
