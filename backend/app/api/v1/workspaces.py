import uuid

from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DbSession
from app.models.workspace import WorkspaceMember
from app.schemas.workspace import (
    AcceptInviteResponse,
    CreateWorkspaceRequest,
    InviteMemberRequest,
    MemberResponse,
    UpdateMemberRoleRequest,
    UpdateWorkspaceRequest,
    WorkspaceDetailResponse,
    WorkspaceResponse,
)
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ---------------------------------------------------------------------------
# Workspace CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    body: CreateWorkspaceRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    ws = await workspace_service.create_workspace(
        db,
        owner=current_user,
        name=body.name,
        slug=body.slug,
        description=body.description,
    )
    count_result = await db.execute(
        select(func.count()).where(
            WorkspaceMember.workspace_id == ws.id,
            WorkspaceMember.invite_status == "accepted",
        )
    )
    return {**ws.__dict__, "member_count": count_result.scalar_one()}


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(current_user: CurrentUser, db: DbSession):
    return await workspace_service.list_workspaces(db, current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    return await workspace_service.get_workspace(db, workspace_id, current_user.id)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    body: UpdateWorkspaceRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    return await workspace_service.update_workspace(
        db,
        workspace_id,
        current_user.id,
        **body.model_dump(exclude_unset=True),
    )


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    await workspace_service.delete_workspace(db, workspace_id, current_user.id)


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------


@router.post("/{workspace_id}/invite", response_model=MemberResponse, status_code=201)
async def invite_member(
    workspace_id: uuid.UUID,
    body: InviteMemberRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    member = await workspace_service.invite_member(
        db,
        workspace_id=workspace_id,
        requesting_user_id=current_user.id,
        email=body.email,
        role=body.role,
    )
    return {
        "id": member.id,
        "user_id": member.user_id,
        "email": member.invited_email,
        "full_name": None,
        "avatar_url": None,
        "role": member.role,
        "invite_status": member.invite_status,
        "created_at": member.created_at,
    }


@router.post("/accept-invite/{invite_token}", response_model=AcceptInviteResponse)
async def accept_invite(
    invite_token: str,
    current_user: CurrentUser,
    db: DbSession,
):
    return await workspace_service.accept_invite(db, invite_token, current_user)


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def list_members(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    detail = await workspace_service.get_workspace(db, workspace_id, current_user.id)
    return detail["members"]


@router.patch("/{workspace_id}/members/{user_id}", response_model=MemberResponse)
async def update_member_role(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    body: UpdateMemberRoleRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    member = await workspace_service.update_member_role(
        db,
        workspace_id=workspace_id,
        target_user_id=user_id,
        requesting_user_id=current_user.id,
        new_role=body.role,
    )
    return {
        "id": member.id,
        "user_id": member.user_id,
        "email": member.invited_email,
        "full_name": None,
        "avatar_url": None,
        "role": member.role,
        "invite_status": member.invite_status,
        "created_at": member.created_at,
    }


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    await workspace_service.remove_member(
        db,
        workspace_id=workspace_id,
        target_user_id=user_id,
        requesting_user_id=current_user.id,
    )
