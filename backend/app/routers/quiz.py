from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.solvers.expected_value import ExpectedValueInput, solve as solve_ev
from app.solvers.madm import MadmInput, solve as solve_madm
from app.solvers.uncertainty import UncertaintyInput, solve as solve_unc

router = APIRouter(prefix="/quiz", tags=["quiz"])

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SECRET_FIELDS = {"answer", "answer_best", "reason", "speak", "panel"}


class GradeBody(BaseModel):
    question_id: str
    method_id: str | None = None
    choice: str | None = None
    compute: dict | None = None


def _bank_path(method_id: str) -> Path:
    if not _SAFE_ID.fullmatch(method_id or ""):
        raise HTTPException(400, "非法题库标识")
    return get_settings().questions_dir / method_id / "bank.json"


def _load_bank(method_id: str) -> list[dict]:
    path = _bank_path(method_id)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _public_item(q: dict) -> dict:
    return {k: v for k, v in q.items() if k not in _SECRET_FIELDS}


def _all_banks() -> dict[str, dict]:
    root = get_settings().questions_dir
    mapping: dict[str, dict] = {}
    if not root.exists():
        return mapping
    for d in sorted(root.iterdir()):
        if d.is_dir() and _SAFE_ID.fullmatch(d.name) and (d / "bank.json").exists():
            for q in _load_bank(d.name):
                mapping[q["id"]] = {**q, "_method": d.name}
    return mapping


@router.get("/{method_id}")
def list_questions(method_id: str):
    bank = _load_bank(method_id)
    return {
        "method_id": method_id,
        "count": len(bank),
        "items": [_public_item(q) for q in bank],
    }


@router.post("/grade")
def grade(body: GradeBody):
    q = None
    if body.method_id and _SAFE_ID.fullmatch(body.method_id):
        for item in _load_bank(body.method_id):
            if item.get("id") == body.question_id:
                q = item
                break
    if not q:
        q = _all_banks().get(body.question_id)
    if not q:
        raise HTTPException(404, "题目不存在")

    if q.get("type") == "choice":
        if not body.choice:
            raise HTTPException(400, "请先选择一个选项")
        correct = body.choice == q.get("answer")
        return {
            "correct": correct,
            "answer": q.get("answer"),
            "reason": q.get("reason"),
            "speak": q.get("speak"),
            "panel": q.get("panel"),
        }

    if q.get("type") == "compute" and body.compute is not None:
        kind = q.get("compute_kind") or "expected_value"
        try:
            if kind == "uncertainty":
                result = solve_unc(UncertaintyInput(**body.compute))
            elif kind == "madm":
                result = solve_madm(MadmInput(**body.compute))
            else:
                result = solve_ev(ExpectedValueInput(**body.compute))
            expected_best = q.get("answer_best")
            correct = result.best == expected_best
            return {
                "correct": correct,
                "answer_best": expected_best,
                "solver": result.model_dump(),
                "speak": result.speak_lines,
                "panel": result.panel_markdown,
            }
        except Exception as e:
            raise HTTPException(400, str(e)) from e

    raise HTTPException(400, "题目类型与提交内容不匹配")
