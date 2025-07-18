import uuid
from typing import Annotated

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_id
from app.utils.exceptions import UnauthorizedError
from app.utils.security import decode_access_token, get_token_subject

# ---------------------------------------------------------------------------
# DB session shorthand
# ---------------------------------------------------------------------------

DbSession = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# JWT extraction — supports both httpOnly cookie and Authorization header
# ---------------------------------------------------------------------------

def _extract_token(
    access_token: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> str:
    if access_token:
        return access_token
    if authorization and authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()
    raise UnauthorizedError("Authentication token not provided")


async def get_current_user(
    db: DbSession,
    token: Annotated[str, Depends(_extract_token)],
) -> User:
    payload = decode_access_token(token)
    user_id_str = get_token_subject(payload)
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError("Malformed token subject")

    user = await get_user_by_id(db, user_id)
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user


async def get_superadmin_user(
    user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    from app.utils.exceptions import ForbiddenError

    if not user.is_superadmin:
        raise ForbiddenError("Superadmin access required")
    return user


# ---------------------------------------------------------------------------
# Type aliases for use in route signatures
# ---------------------------------------------------------------------------

CurrentUser = Annotated[User, Depends(get_current_active_user)]
SuperAdminUser = Annotated[User, Depends(get_superadmin_user)]
