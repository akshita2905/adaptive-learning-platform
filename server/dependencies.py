"""FastAPI dependencies: auth and DB."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth_utils import decode_token
from config import get_settings

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> str:
    """Require a valid Bearer JWT and return the user id (subject)."""
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    uid = decode_token(creds.credentials, get_settings())
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return uid
