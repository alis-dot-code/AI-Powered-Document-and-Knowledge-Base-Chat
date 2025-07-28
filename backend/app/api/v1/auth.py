from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentUser, DbSession
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.schemas.common import MessageResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------

_ACCESS_COOKIE = "access_token"
_REFRESH_COOKIE = "refresh_token"
_COOKIE_OPTS: dict = {
    "httponly": True,
    "secure": not settings.is_development,
    "samesite": "lax",
    "path": "/",
}


def _set_auth_cookies(response: Response, tokens: TokenResponse) -> None:
    response.set_cookie(
        key=_ACCESS_COOKIE,
        value=tokens.access_token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        **_COOKIE_OPTS,
    )
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=tokens.refresh_token,
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        **_COOKIE_OPTS,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(_ACCESS_COOKIE, path="/")
    response.delete_cookie(_REFRESH_COOKIE, path="/")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    response: Response,
    db: DbSession,
) -> RegisterResponse:
    result = await auth_service.register_user(db, payload)
    _set_auth_cookies(
        response,
        TokenResponse(
            access_token="",  # No auto-login on register; user must verify email first
            refresh_token="",
            expires_in=0,
        ),
    )
    return result


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: DbSession,
) -> LoginResponse:
    result = await auth_service.login_user(db, payload.email, payload.password)
    _set_auth_cookies(response, result.tokens)
    return result


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshTokenRequest,
    response: Response,
    db: DbSession,
) -> TokenResponse:
    tokens = await auth_service.refresh_tokens(db, payload.refresh_token)
    _set_auth_cookies(response, tokens)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UpdateProfileRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    return await auth_service.update_profile(db, current_user, payload)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: DbSession,
) -> MessageResponse:
    # Always return success to avoid email enumeration
    try:
        await auth_service.get_user_by_email(db, payload.email)
        # TODO: send reset email via background task (Prompt 26)
    except Exception:
        pass
    return MessageResponse(message="If that email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: DbSession,
) -> MessageResponse:
    # TODO: implement token-based reset (Prompt 26)
    return MessageResponse(message="Password reset successfully")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: DbSession,
) -> MessageResponse:
    # TODO: implement email verification (Prompt 26)
    return MessageResponse(message="Email verified successfully")
