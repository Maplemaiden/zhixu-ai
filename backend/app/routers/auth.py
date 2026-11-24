from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.deps import get_bearer_token, require_user
from app.services import user_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RegisterBody(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=4, max_length=128)
    display_name: str = Field(default="", max_length=64)


@router.post("/login")
def login(body: LoginBody):
    user = user_db.authenticate(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = user_db.create_token(user["id"])
    return {"token": token, "user": user}


@router.post("/register")
def register(body: RegisterBody):
    try:
        user = user_db.register_user(body.username, body.password, body.display_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    token = user_db.create_token(user["id"])
    return {"token": token, "user": user}


@router.get("/me")
def me(user=Depends(require_user)):
    return {"user": user}


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    token = get_bearer_token(authorization)
    if token:
        user_db.revoke_token(token)
    return {"ok": True}


@router.get("/demo_accounts")
def demo_accounts():
    """演示用账号提示（不含密码哈希，仅口令说明）。"""
    return {
        "accounts": [
            {"username": u["username"], "password": u["password"], "display_name": u["display_name"]}
            for u in user_db.DEMO_USERS
        ],
        "tags": user_db.TAG_PRESETS,
    }
