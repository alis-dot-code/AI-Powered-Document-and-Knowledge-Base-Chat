import secrets
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.utils.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)

# Role hierarchy — higher index = more privileged
_ROLE_RANK: dict[str, int] = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}


def _rank(role: str) -> int:
    return _ROLE_RANK.get(role, -1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_workspace_or_404(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = result.scalar_one_or_none()
    if ws is None:
        raise NotFoundError("Workspace not found")
    return ws


async def _get_membership(
    db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> WorkspaceMember | None:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.invite_status == "accepted",
        )
    )
    return result.scalar_one_or_none()


async def _require_membership(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    min_role: str = "viewer",
) -> WorkspaceMember:
    mem = await _get_membership(db, workspace_id, user_id)
    if mem is None or _rank(mem.role) < _rank(min_role):
        raise ForbiddenError("Insufficient workspace permissions")
    return mem


# ---------------------------------------------------------------------------
# Workspace CRUD
# ---------------------------------------------------------------------------


async def create_workspace(
    db: AsyncSession,
    owner: User,
    name: str,
    slug: str,
    description: str | None,
) -> Workspace:
    # Check slug uniqueness
    exists = await db.execute(select(Workspace).where(Workspace.slug == slug))
    if exists.scalar_one_or_none():
        raise ConflictError("A workspace with this slug already exists")

    ws = Workspace(
        owner_id=owner.id,
        name=name,
        slug=slug,
        description=description,
    )
    db.add(ws)
    await db.flush()

    # Owner is automatically an accepted member with role=owner
    member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=owner.id,
        role="owner",
        invite_status="accepted",
    )
    db.add(member)
    await db.flush()

    return ws


async def list_workspaces(db: AsyncSession, user_id: uuid.UUID) -> list[dict[str, Any]]:
    """Return workspaces the user is an accepted member of, with member_count."""
    rows = await db.execute(
        select(Workspace, WorkspaceMember)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.invite_status == "accepted",
        )
        .order_by(Workspace.created_at.desc())
    )
    pairs = rows.all()

    ws_ids = [ws.id for ws, _ in pairs]
    if not ws_ids:
        return []

    # Batch member counts
    count_rows = await db.execute(
        select(WorkspaceMember.workspace_id, func.count().label("cnt"))
        .where(
            WorkspaceMember.workspace_id.in_(ws_ids),
            WorkspaceMember.invite_status == "accepted",
        )
        .group_by(WorkspaceMember.workspace_id)
    )
    counts: dict[uuid.UUID, int] = {r.workspace_id: r.cnt for r in count_rows}

    results = []
    for ws, mem in pairs:
        results.append({**ws.__dict__, "member_count": counts.get(ws.id, 1)})
    return results


async def get_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
) -> dict[str, Any]:
    mem = await _require_membership(db, workspace_id, requesting_user_id, min_role="viewer")
    ws_result = await db.execute(
        select(Workspace)
        .options(
            selectinload(Workspace.members).selectinload(WorkspaceMember.user)
        )
        .where(Workspace.id == workspace_id)
    )
    ws = ws_result.scalar_one_or_none()
    if ws is None:
        raise NotFoundError("Workspace not found")

    count_result = await db.execute(
        select(func.count()).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.invite_status == "accepted",
        )
    )
    member_count = count_result.scalar_one()

    members = []
    for m in ws.members:
        members.append({
            "id": m.id,
            "user_id": m.user_id,
            "email": m.user.email if m.user else m.invited_email,
            "full_name": m.user.full_name if m.user else None,
            "avatar_url": m.user.avatar_url if m.user else None,
            "role": m.role,
            "invite_status": m.invite_status,
            "created_at": m.created_at,
        })

    return {
        **ws.__dict__,
        "member_count": member_count,
        "members": members,
        "current_user_role": mem.role,
    }


async def update_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
    **kwargs: Any,
) -> dict[str, Any]:
    await _require_membership(db, workspace_id, requesting_user_id, min_role="admin")
    ws = await _get_workspace_or_404(db, workspace_id)

    for key, value in kwargs.items():
        if value is not None:
            setattr(ws, key, value)

    await db.flush()
    count_result = await db.execute(
        select(func.count()).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.invite_status == "accepted",
        )
    )
    return {**ws.__dict__, "member_count": count_result.scalar_one()}


async def delete_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
) -> None:
    ws = await _get_workspace_or_404(db, workspace_id)
    if ws.owner_id != requesting_user_id:
        raise ForbiddenError("Only the workspace owner can delete it")
    await db.delete(ws)
    await db.flush()


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------


async def invite_member(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
    email: str,
    role: str,
) -> WorkspaceMember:
    await _require_membership(db, workspace_id, requesting_user_id, min_role="admin")

    # Check if already a member / pending invite
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.invited_email == email,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("This email already has a pending or active membership")

    # Check if the email belongs to an existing user who is already a member
    user_result = await db.execute(select(User).where(User.email == email))
    existing_user = user_result.scalar_one_or_none()
    if existing_user:
        active = await _get_membership(db, workspace_id, existing_user.id)
        if active:
            raise ConflictError("User is already a member of this workspace")

    invite_token = secrets.token_urlsafe(32)
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=existing_user.id if existing_user else None,
        role=role,
        invite_status="pending",
        invite_token=invite_token,
        invited_email=email,
    )
    db.add(member)
    await db.flush()
    return member


async def accept_invite(
    db: AsyncSession,
    invite_token: str,
    accepting_user: User,
) -> dict[str, Any]:
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.invite_token == invite_token)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise NotFoundError("Invite not found or already used")
    if member.invite_status != "pending":
        raise ValidationError("Invite has already been accepted or is invalid")
    if member.invited_email and member.invited_email != accepting_user.email:
        raise ForbiddenError("This invite was sent to a different email address")

    member.user_id = accepting_user.id
    member.invite_status = "accepted"
    member.invite_token = None
    await db.flush()

    ws_data = await get_workspace(db, member.workspace_id, accepting_user.id)
    return {"workspace": ws_data, "role": member.role}


async def update_member_role(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
    new_role: str,
) -> WorkspaceMember:
    requester_mem = await _require_membership(db, workspace_id, requesting_user_id, min_role="admin")

    if target_user_id == requesting_user_id:
        raise ValidationError("Cannot change your own role")

    target_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user_id,
            WorkspaceMember.invite_status == "accepted",
        )
    )
    target_mem = target_result.scalar_one_or_none()
    if target_mem is None:
        raise NotFoundError("Member not found")

    # Cannot promote/demote to a role equal to or above your own (unless owner)
    if requester_mem.role != "owner" and _rank(new_role) >= _rank(requester_mem.role):
        raise ForbiddenError("Cannot assign a role equal to or higher than your own")

    # Cannot demote the owner
    if target_mem.role == "owner":
        raise ForbiddenError("Cannot change the owner's role")

    target_mem.role = new_role
    await db.flush()
    return target_mem


async def remove_member(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
) -> None:
    ws = await _get_workspace_or_404(db, workspace_id)

    if target_user_id == ws.owner_id:
        raise ForbiddenError("Cannot remove the workspace owner")

    # Members can leave themselves; admins/owners can remove others
    if target_user_id != requesting_user_id:
        await _require_membership(db, workspace_id, requesting_user_id, min_role="admin")

    target_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user_id,
        )
    )
    target_mem = target_result.scalar_one_or_none()
    if target_mem is None:
        raise NotFoundError("Member not found")

    await db.delete(target_mem)
    await db.flush()
