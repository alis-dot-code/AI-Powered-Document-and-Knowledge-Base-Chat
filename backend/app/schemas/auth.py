import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import AppSchema


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255, strip_whitespace=True)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    avatar_url: str | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserResponse(AppSchema):
    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: str | None
    is_active: bool
    is_superadmin: bool
    email_verified: bool
    last_login_at: datetime | None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class RegisterResponse(BaseModel):
    user: UserResponse
    message: str = "Account created. Please verify your email."
