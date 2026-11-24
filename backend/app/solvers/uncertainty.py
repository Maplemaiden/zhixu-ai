"""不确定型决策五大准则：纯程序计算。"""
from __future__ import annotations

from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field

Criterion = Literal["optimistic", "pessimistic", "hurwicz", "regret", "laplace"]


class UncertaintyInput(BaseModel):
    alternatives: list[str] = Field(..., min_length=1)
    states: list[str] = Field(..., min_length=1)
    payoffs: list[list[float]]
    sense: Literal["max", "min"] = "max"  # 收益表用 max；若是损失表可 min
    criterion: Criterion = "optimistic"
    alpha: float = Field(0.6, ge=0, le=1, description="折中系数，越接近1越乐观（收益型）")
    decimals: int = 4


class UncertaintyResult(BaseModel):
    criterion: str
    criterion_name: str
    scores: dict[str, float]
    best: str
    best_value: float
    steps: list[dict[str, Any]]
    panel_markdown: str
    speak_lines: list[str]


NAMES = {
    "optimistic": "乐观准则（最大最大）",
    "pessimistic": "悲观准则（最大最小）",
    "hurwicz": "折中准则（赫威斯）",
    "regret": "后悔值准则（最小最大后悔）",
    "laplace": "等概率准则（拉普拉斯）",
}


def _validate(data: UncertaintyInput) -> None:
    n_a, n_s = len(data.alternatives), len(data.states)
    if len(data.payoffs) != n_a:
        raise ValueError("收益矩阵行数与方案数不一致")
    for i, row in enumerate(data.payoffs):
        if len(row) != n_s:
            raise ValueError(f"方案 {data.alternatives[i]} 列数与状态数不一致")


def solve(data: UncertaintyInput) -> UncertaintyResult:
    _validate(data)
    m = np.asarray(data.payoffs, dtype=float)
    alts = data.alternatives
    is_gain = data.sense == "max"

    scores: dict[str, float] = {}
    detail_lines: list[str] = []

    if data.criterion == "optimistic":
        # 收益：每行取 max，再取最大；损失：每行取 min，再取最小
        row = m.max(axis=1) if is_gain else m.min(axis=1)
        for i, a in enumerate(alts):
            scores[a] = round(float(row[i]), data.decimals)
            detail_lines.append(f"{a} 的极端值 = {scores[a]}")
        best_idx = int(np.argmax(row) if is_gain else np.argmin(row))

    elif data.criterion == "pessimistic":
        row = m.min(axis=1) if is_gain else m.max(axis=1)
        for i, a in enumerate(alts):
            scores[a] = round(float(row[i]), data.decimals)
            detail_lines.append(f"{a} 的保守值 = {scores[a]}")
        best_idx = int(np.argmax(row) if is_gain else np.argmin(row))

    elif data.criterion == "hurwicz":
        alpha = data.alpha
        if is_gain:
            row = alpha * m.max(axis=1) + (1 - alpha) * m.min(axis=1)
        else:
            row = alpha * m.min(axis=1) + (1 - alpha) * m.max(axis=1)
        for i, a in enumerate(alts):
            scores[a] = round(float(row[i]), data.decimals)
            detail_lines.append(f"{a} 折中值(α={alpha}) = {scores[a]}")
        best_idx = int(np.argmax(row) if is_gain else np.argmin(row))

    elif data.criterion == "regret":
        if is_gain:
            ideal = m.max(axis=0)
            regret = ideal - m
        else:
            ideal = m.min(axis=0)
            regret = m - ideal
        row = regret.max(axis=1)
        for i, a in enumerate(alts):
            scores[a] = round(float(row[i]), data.decimals)
            detail_lines.append(f"{a} 的最大后悔值 = {scores[a]}")
        best_idx = int(np.argmin(row))

    elif data.criterion == "laplace":
        row = m.mean(axis=1)
        for i, a in enumerate(alts):
            scores[a] = round(float(row[i]), data.decimals)
            detail_lines.append(f"{a} 的等概率均值 = {scores[a]}")
        best_idx = int(np.argmax(row) if is_gain else np.argmin(row))
    else:
        raise ValueError("未知准则")

    best = alts[best_idx]
    best_value = scores[best]
    name = NAMES[data.criterion]

    panel = [
        f"## 不确定型决策 · {name}",
        "",
        "### 步骤 1：确认收益（损失）表",
        f"- 方案：{', '.join(alts)}",
        f"- 状态：{', '.join(data.states)}（概率未知）",
        "",
        "### 步骤 2：按准则计算各方案指标",
        *[f"- {x}" for x in detail_lines],
        "",
        "### 步骤 3：决策",
        f"- **最优方案：{best}（指标值 {best_value}）**",
        "",
        "> 数值由程序计算；不同准则可能选出不同方案，这与决策者风险态度有关。",
    ]
    speak = [
        f"下面用{name}处理这道不确定型决策题。",
        "第一步，列出各方案在不同自然状态下的收益，注意此时概率未知。",
        "第二步，" + "；".join(detail_lines) + "。",
        f"第三步，按该准则选择方案{best}。",
    ]

    return UncertaintyResult(
        criterion=data.criterion,
        criterion_name=name,
        scores=scores,
        best=best,
        best_value=best_value,
        steps=[
            {"id": 1, "name": "列出收益表", "values": {"alternatives": alts, "states": data.states}},
            {"id": 2, "name": "按准则计算", "values": {"scores": scores, "details": detail_lines}},
            {"id": 3, "name": "选优", "values": {"best": best, "best_value": best_value}},
        ],
        panel_markdown="\n".join(panel),
        speak_lines=speak,
    )
