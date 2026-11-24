from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.deps import require_user
from app.services import user_db

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteCreate(BaseModel):
    method_id: str = Field(min_length=1, max_length=80)
    quote: str = Field(min_length=1, max_length=2000)
    section_index: int = Field(default=0, ge=0, le=200)
    color: str = Field(default="amber", max_length=20)
    tag: str = Field(default="", max_length=40)
    remark: str = Field(default="", max_length=500)


class NoteUpdate(BaseModel):
    color: str | None = Field(default=None, max_length=20)
    tag: str | None = Field(default=None, max_length=40)
    remark: str | None = Field(default=None, max_length=500)


@router.get("")
def list_notes(
    method_id: str | None = Query(default=None),
    user=Depends(require_user),
):
    items = user_db.list_notes(user["id"], method_id=method_id)
    return {"items": items, "count": len(items)}


@router.post("")
def create_note(body: NoteCreate, user=Depends(require_user)):
    try:
        note = user_db.create_note(
            user["id"],
            method_id=body.method_id,
            quote=body.quote,
            section_index=body.section_index,
            color=body.color,
            tag=body.tag,
            remark=body.remark,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"item": note}


@router.patch("/{note_id}")
def patch_note(note_id: str, body: NoteUpdate, user=Depends(require_user)):
    note = user_db.update_note(
        user["id"],
        note_id,
        color=body.color,
        tag=body.tag,
        remark=body.remark,
    )
    if not note:
        raise HTTPException(status_code=404, detail="标注不存在")
    return {"item": note}


@router.delete("/{note_id}")
def remove_note(note_id: str, user=Depends(require_user)):
    ok = user_db.delete_note(user["id"], note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="标注不存在")
    return {"ok": True}
