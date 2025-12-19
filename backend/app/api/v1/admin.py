"""
Admin API — superadmin-only endpoints.
All routes require is_superadmin=True on the authenticated user.
"""
import uuid

from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import DbSession, SuperAdminUser
from app.models.document import Document
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.auth import UpdateProfileRequest, UserResponse
from app.schemas.common import PaginationParams
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_stats(db: DbSession, _admin: SuperAdminUser):
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    ws_count = (await db.execute(select(func.count(Workspace.id)))).scalar() or 0
    doc_count = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    return {
        "total_users": user_count,
        "total_workspaces": ws_count,
        "total_documents": doc_count,
    }


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@router.get("/users")
async def list_users(
    db: DbSession,
    _admin: SuperAdminUser,
    page: int = 1,
    page_size: int = 20,
):
    offset = (page - 1) * page_size
    total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()
    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UpdateProfileRequest,
    db: DbSession,
    _admin: SuperAdminUser,
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------

@router.get("/workspaces")
async def list_workspaces(
    db: DbSession,
    _admin: SuperAdminUser,
    page: int = 1,
    page_size: int = 20,
):
    offset = (page - 1) * page_size
    total = (await db.execute(select(func.count(Workspace.id)))).scalar() or 0
    result = await db.execute(
        select(Workspace).order_by(Workspace.created_at.desc()).offset(offset).limit(page_size)
    )
    workspaces = result.scalars().all()
    return {
        "items": [
            {
                "id": str(ws.id),
                "name": ws.name,
                "slug": ws.slug,
                "owner_id": str(ws.owner_id),
                "created_at": ws.created_at.isoformat(),
            }
            for ws in workspaces
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
