#!/usr/bin/env python3
"""
Create a superadmin user.

Usage:
    cd backend
    python ../scripts/create_superuser.py admin@example.com MyPassword1!
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import hash_password


async def create_superuser(email: str, password: str, full_name: str = "Admin"):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_superadmin = True
            existing.is_active = True
            await db.commit()
            print(f"Updated existing user '{email}' → superadmin=True")
            return

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=True,
            is_superadmin=True,
            email_verified=True,
        )
        db.add(user)
        await db.commit()
        print(f"Created superadmin: {email}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: create_superuser.py <email> <password> [full_name]")
        sys.exit(1)
    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Admin"
    asyncio.run(create_superuser(email, password, full_name))
