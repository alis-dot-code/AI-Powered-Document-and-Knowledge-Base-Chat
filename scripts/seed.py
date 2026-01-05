#!/usr/bin/env python3
"""
Seed script — populates DocMind with demo data.

Usage:
    cd backend
    python ../scripts/seed.py

Requires DATABASE_URL in environment or .env file.
"""
import asyncio
import os
import sys
import uuid

# Allow running from repo root or scripts/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.chat import ChatSession, ChatMessage
from app.utils.security import hash_password


DEMO_EMAIL = "demo@docmind.ai"
DEMO_PASSWORD = "Demo1234!"
DEMO_WORKSPACE_SLUG = "demo-workspace"


async def seed():
    async with AsyncSessionLocal() as db:
        # ------------------------------------------------------------------ #
        # 1. Demo user
        # ------------------------------------------------------------------ #
        result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=uuid.uuid4(),
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Demo User",
                is_active=True,
                email_verified=True,
            )
            db.add(user)
            await db.flush()
            print(f"  Created user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print(f"  User already exists: {DEMO_EMAIL}")

        # ------------------------------------------------------------------ #
        # 2. Demo workspace
        # ------------------------------------------------------------------ #
        result = await db.execute(
            select(Workspace).where(Workspace.slug == DEMO_WORKSPACE_SLUG)
        )
        workspace = result.scalar_one_or_none()

        if not workspace:
            workspace = Workspace(
                id=uuid.uuid4(),
                owner_id=user.id,
                name="Demo Workspace",
                slug=DEMO_WORKSPACE_SLUG,
                description="A pre-seeded workspace to explore DocMind.",
            )
            db.add(workspace)
            await db.flush()

            member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=user.id,
                role="owner",
                invite_status="accepted",
            )
            db.add(member)
            await db.flush()
            print(f"  Created workspace: {workspace.name}")
        else:
            print(f"  Workspace already exists: {workspace.name}")

        # ------------------------------------------------------------------ #
        # 3. Demo chat session with a welcome message
        # ------------------------------------------------------------------ #
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.workspace_id == workspace.id,
                ChatSession.title == "Welcome Chat",
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            session = ChatSession(
                workspace_id=workspace.id,
                user_id=user.id,
                title="Welcome Chat",
            )
            db.add(session)
            await db.flush()

            msg = ChatMessage(
                session_id=session.id,
                workspace_id=workspace.id,
                role="assistant",
                content=(
                    "Welcome to DocMind! 👋\n\n"
                    "Upload a PDF, DOCX, TXT, or CSV — or scrape a URL — then ask me "
                    "anything about it. I'll answer with citations pointing to the "
                    "exact source passages.\n\n"
                    "Get started by uploading a document from the Documents page."
                ),
                token_count=0,
            )
            db.add(msg)
            await db.flush()
            print("  Created demo chat session with welcome message")

        await db.commit()

    print("\nSeed complete.")
    print(f"  Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print(f"  Workspace: {DEMO_WORKSPACE_SLUG}")


if __name__ == "__main__":
    asyncio.run(seed())
