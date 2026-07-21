"""Password hashing and JWT creation/verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import Settings, get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain password matches the stored hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, settings: Settings | None = None) -> str:
    """Create a signed JWT with subject (user id) and expiry."""
    s = settings or get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=s.jwt_exp_hours)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def decode_token(token: str, settings: Settings | None = None) -> str | None:
    """Decode JWT and return subject user id, or None if invalid."""
    s = settings or get_settings()
    try:
        data = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
        sub = data.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None
