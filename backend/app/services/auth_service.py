import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.auth import (
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.utils.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_token_subject,
    hash_password,
    verify_password,
)


def _build_token_response(user_id: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def _to_user_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

async def register_user(
    db: AsyncSession, payload: RegisterRequest
) -> RegisterResponse:
    # Check uniqueness
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise EmailAlreadyExistsError()

    user = User(
        id=uuid.uuid4(),
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        is_active=True,
        email_verified=False,
    )
    db.add(user)
    await db.flush()  # get the ID without committing

    return RegisterResponse(user=_to_user_response(user))


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def login_user(
    db: AsyncSession, email: str, password: str
) -> LoginResponse:
    user = await db.scalar(select(User).where(User.email == email.lower().strip()))

    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise InvalidCredentialsError()

    # Update last_login_at
    user.last_login_at = datetime.now(UTC)
    await db.flush()

    return LoginResponse(
        user=_to_user_response(user),
        tokens=_build_token_response(str(user.id)),
    )


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------

async def refresh_tokens(
    db: AsyncSession, refresh_token: str
) -> TokenResponse:
    payload = decode_refresh_token(refresh_token)
    user_id = get_token_subject(payload)

    user = await db.scalar(select(User).where(User.id == uuid.UUID(user_id)))
    if not user or not user.is_active:
        raise InvalidTokenError("User not found or inactive")

    return _build_token_response(str(user.id))


# ---------------------------------------------------------------------------
# Get current user
# ---------------------------------------------------------------------------

async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise NotFoundError("User")
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User:
    user = await db.scalar(select(User).where(User.email == email.lower().strip()))
    if not user:
        raise NotFoundError("User")
    return user


# ---------------------------------------------------------------------------
# Update profile
# ---------------------------------------------------------------------------

async def update_profile(
    db: AsyncSession, user: User, payload: UpdateProfileRequest
) -> UserResponse:
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    await db.flush()
    return _to_user_response(user)


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

async def change_password(
    db: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise InvalidCredentialsError()
    user.password_hash = hash_password(new_password)
    await db.flush()
