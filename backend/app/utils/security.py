import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.utils.exceptions import InvalidTokenError

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, extra: dict[str, Any] | None = None) -> str:
    return _create_token(
        subject=user_id,
        token_type=_ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        extra_claims=extra,
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        token_type=_REFRESH_TOKEN_TYPE,
        expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return _decode_token(token, expected_type=_ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> dict[str, Any]:
    return _decode_token(token, expected_type=_REFRESH_TOKEN_TYPE)


def _decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise InvalidTokenError()

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected {expected_type} token")

    return payload


def get_token_subject(payload: dict[str, Any]) -> str:
    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token missing subject")
    return sub


# ---------------------------------------------------------------------------
# API key generation
# ---------------------------------------------------------------------------

def generate_api_key() -> tuple[str, str, str]:
    """
    Returns (raw_key, key_prefix, key_hash).
    raw_key  — shown once to the user (dm_live_<32 hex chars>)
    key_prefix — first 12 chars stored in DB for lookup
    key_hash   — bcrypt hash stored in DB for verification
    """
    raw = "dm_" + secrets.token_hex(32)
    prefix = raw[:12]
    hashed = _pwd_context.hash(raw)
    return raw, prefix, hashed


def verify_api_key(raw: str, hashed: str) -> bool:
    return _pwd_context.verify(raw, hashed)


# ---------------------------------------------------------------------------
# Email verification / password-reset tokens (opaque, short-lived)
# ---------------------------------------------------------------------------

def generate_opaque_token() -> str:
    return secrets.token_urlsafe(32)
