import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


WorkspaceRole = Literal["owner", "admin", "member", "viewer"]
InviteStatus = Literal["pending", "accepted"]

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(None, max_length=1000)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError(
                "Slug must be lowercase alphanumeric with hyphens (no leading/trailing hyphens)"
            )
        return v


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    logo_url: str | None = None


class InviteMemberRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    role: Literal["admin", "member", "viewer"] = "member"


class UpdateMemberRoleRequest(BaseModel):
    role: Literal["admin", "member", "viewer"]


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class MemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    email: str
    full_name: str | None
    avatar_url: str | None
    role: WorkspaceRole
    invite_status: InviteStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    member_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceDetailResponse(WorkspaceResponse):
    members: list[MemberResponse]
    current_user_role: WorkspaceRole


class AcceptInviteResponse(BaseModel):
    workspace: WorkspaceResponse
    role: WorkspaceRole
