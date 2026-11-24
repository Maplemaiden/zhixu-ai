from __future__ import annotations

from fastapi import Header, HTTPException

from app.services import user_db


def get_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def require_user(authorization: str | None = Header(default=None)):
    token = get_bearer_token(authorization)
    user = user_db.user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user
