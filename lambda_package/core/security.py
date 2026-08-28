"""Password hashing and JWT creation/verification."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt

from core.config import get_settings

BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    encoded = password.encode("utf-8")
    if len(encoded) > BCRYPT_MAX_BYTES:
        raise ValueError(f"Password exceeds bcrypt's {BCRYPT_MAX_BYTES}-byte limit.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Malformed hash in the database, or an over-length password.
        return False


def create_access_token(user_id: int, role: str) -> str:
    """Issue a signed JWT for a user."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises jwt.PyJWTError on any failure."""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


PASSWORD_RESET_PURPOSE = "password_reset"
PASSWORD_RESET_EXPIRE_MINUTES = 15


def create_password_reset_token(user_id: UUID) -> str:
    """Issue a short-lived, purpose-scoped JWT for resetting a password.

    Distinct from create_access_token via the "purpose" claim, so a leaked
    reset token can't be replayed as a normal Bearer access token.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "purpose": PASSWORD_RESET_PURPOSE,
        "iat": now,
        "exp": now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_password_reset_token(token: str) -> UUID:
    """Decode a password-reset token and return the target user id.

    Raises jwt.PyJWTError if the token is invalid/expired, or ValueError if
    it's a well-formed JWT that isn't a password-reset token.
    """
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if payload.get("purpose") != PASSWORD_RESET_PURPOSE:
        raise ValueError("Not a password reset token.")
    return UUID(payload["sub"])