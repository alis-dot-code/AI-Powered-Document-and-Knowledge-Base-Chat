"""Initial schema — all tables with pgvector

Revision ID: 001
Revises:
Create Date: 2026-04-13 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ------------------------------------------------------------------
    # ENUM types
    # ------------------------------------------------------------------
    workspace_role = postgresql.ENUM(
        "owner", "admin", "editor", "viewer",
        name="workspace_role", create_type=False,
    )
    workspace_role.create(op.get_bind(), checkfirst=True)

    document_status = postgresql.ENUM(
        "pending", "processing", "chunking", "embedding", "completed", "failed",
        name="document_status", create_type=False,
    )
    document_status.create(op.get_bind(), checkfirst=True)

    document_source = postgresql.ENUM(
        "upload", "url",
        name="document_source", create_type=False,
    )
    document_source.create(op.get_bind(), checkfirst=True)

    message_role = postgresql.ENUM(
        "user", "assistant", "system",
        name="message_role", create_type=False,
    )
    message_role.create(op.get_bind(), checkfirst=True)

    usage_type = postgresql.ENUM(
        "embedding", "query", "chat_completion", "document_ingestion",
        name="usage_type", create_type=False,
    )
    usage_type.create(op.get_bind(), checkfirst=True)

    subscription_status = postgresql.ENUM(
        "active", "past_due", "canceled", "trialing", "unpaid", "incomplete",
        name="subscription_status", create_type=False,
    )
    subscription_status.create(op.get_bind(), checkfirst=True)

    plan_tier = postgresql.ENUM(
        "free", "starter", "pro", "enterprise",
        name="plan_tier", create_type=False,
    )
    plan_tier.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # USERS
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # ------------------------------------------------------------------
    # WORKSPACES
    # ------------------------------------------------------------------
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("settings", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("max_documents", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("max_queries_day", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_workspaces_slug", "workspaces", ["slug"])
    op.create_index("idx_workspaces_owner", "workspaces", ["owner_id"])

    # ------------------------------------------------------------------
    # WORKSPACE MEMBERS
    # ------------------------------------------------------------------
    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Enum("owner", "admin", "editor", "viewer",
                                  name="workspace_role"), nullable=False,
                  server_default="viewer"),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invited_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("accepted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )
    op.create_index("idx_wm_workspace", "workspace_members", ["workspace_id"])
    op.create_index("idx_wm_user", "workspace_members", ["user_id"])

    # ------------------------------------------------------------------
    # DOCUMENTS
    # ------------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("file_name", sa.String(512), nullable=True),
        sa.Column("file_url", sa.String(1024), nullable=True),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("source_type",
                  sa.Enum("upload", "url", name="document_source"),
                  nullable=False, server_default="upload"),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status",
                  sa.Enum("pending", "processing", "chunking", "embedding",
                          "completed", "failed", name="document_status"),
                  nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processing_started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_documents_workspace", "documents", ["workspace_id"])
    op.create_index("idx_documents_status", "documents", ["status"])
    op.create_index("idx_documents_workspace_status", "documents",
                    ["workspace_id", "status"])

    # ------------------------------------------------------------------
    # DOCUMENT CHUNKS (with vector column)
    # ------------------------------------------------------------------
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("char_start", sa.Integer(), nullable=True),
        sa.Column("char_end", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_chunks_document", "document_chunks", ["document_id"])
    op.create_index("idx_chunks_workspace", "document_chunks", ["workspace_id"])

    # HNSW index for approximate nearest-neighbor vector search
    op.execute(
        """
        CREATE INDEX idx_chunks_embedding
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # ------------------------------------------------------------------
    # CHAT SESSIONS
    # ------------------------------------------------------------------
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("is_widget", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_sessions_workspace", "chat_sessions", ["workspace_id"])
    op.create_index("idx_sessions_user", "chat_sessions", ["user_id"])

    # ------------------------------------------------------------------
    # CHAT MESSAGES
    # ------------------------------------------------------------------
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role",
                  sa.Enum("user", "assistant", "system", name="message_role"),
                  nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("model_used", sa.String(64), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_messages_session", "chat_messages", ["session_id"])
    op.create_index("idx_messages_session_created", "chat_messages",
                    ["session_id", "created_at"])

    # ------------------------------------------------------------------
    # CITATIONS
    # ------------------------------------------------------------------
    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_citations_message", "citations", ["message_id"])

    # ------------------------------------------------------------------
    # API KEYS
    # ------------------------------------------------------------------
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("allowed_origins", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_apikeys_workspace", "api_keys", ["workspace_id"])
    op.create_index("idx_apikeys_prefix", "api_keys", ["key_prefix"])

    # ------------------------------------------------------------------
    # USAGE LOGS
    # ------------------------------------------------------------------
    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("usage_type",
                  sa.Enum("embedding", "query", "chat_completion", "document_ingestion",
                          name="usage_type"),
                  nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_usage_workspace", "usage_logs", ["workspace_id"])
    op.create_index("idx_usage_workspace_created", "usage_logs",
                    ["workspace_id", "created_at"])
    op.create_index("idx_usage_workspace_type_created", "usage_logs",
                    ["workspace_id", "usage_type", "created_at"])

    # ------------------------------------------------------------------
    # SUBSCRIPTIONS
    # ------------------------------------------------------------------
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False,
                  unique=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True, unique=True),
        sa.Column("plan",
                  sa.Enum("free", "starter", "pro", "enterprise", name="plan_tier"),
                  nullable=False, server_default="free"),
        sa.Column("status",
                  sa.Enum("active", "past_due", "canceled", "trialing", "unpaid",
                          "incomplete", name="subscription_status"),
                  nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False,
                  server_default="false"),
        sa.Column("monthly_query_limit", sa.Integer(), nullable=False,
                  server_default="100"),
        sa.Column("monthly_doc_limit", sa.Integer(), nullable=False,
                  server_default="10"),
        sa.Column("monthly_token_limit", sa.Integer(), nullable=False,
                  server_default="100000"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_subscriptions_stripe_customer", "subscriptions",
                    ["stripe_customer_id"])
    op.create_index("idx_subscriptions_stripe_sub", "subscriptions",
                    ["stripe_subscription_id"])

    # ------------------------------------------------------------------
    # auto-update updated_at trigger function
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """
    )

    for table in [
        "users", "workspaces", "documents", "chat_sessions", "subscriptions",
    ]:
        op.execute(
            f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
            """
        )


def downgrade() -> None:
    # Drop triggers
    for table in [
        "users", "workspaces", "documents", "chat_sessions", "subscriptions",
    ]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse dependency order
    for table in [
        "subscriptions",
        "usage_logs",
        "api_keys",
        "citations",
        "chat_messages",
        "chat_sessions",
        "document_chunks",
        "documents",
        "workspace_members",
        "workspaces",
        "users",
    ]:
        op.drop_table(table)

    # Drop ENUMs
    for enum_name in [
        "plan_tier", "subscription_status", "usage_type",
        "message_role", "document_source", "document_status", "workspace_role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    op.execute('DROP EXTENSION IF EXISTS vector')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
