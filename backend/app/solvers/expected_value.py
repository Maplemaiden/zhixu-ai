"""期望值准则：纯程序计算，不依赖大模型。"""
from __future__ import annotations

from typing import Any

import numpy as np
from pydantic import BaseModel, Field, field_validator


class ExpectedValueInput(BaseModel):
    alternatives: list[str] = Field(..., min_length=1, description="方案名")
    states: list[str] = Field(..., min_length=1, description="自然状态名")
    probs: list[float] = Field(..., min_length=1, description="各状态概率")
    payoffs: list[list[float]] = Field(..., description="收益矩阵 [方案][状态]")
    sense: str = Field("max", description="max=收益最大 / min=损失最小")
    decimals: int = 4

    @field_validator("probs")
    @classmethod
    def probs_nonneg(cls, v: list[float]) -> list[float]:
        if any(not np.isfinite(p) for p in v):
            raise ValueError("概率包含非法数值")
        if any(p < 0 or p > 1 for p in v):
            raise ValueError("概率须在 0 到 1 之间")
        return v


class ExpectedValueResult(BaseModel):
    expectations: dict[str, float]
    best: str
    best_value: float
    all_equal: bool = False
    steps: list[dict[str, Any]]
    panel_markdown: str
    speak_lines: list[str]


def validate_shape(data: ExpectedValueInput) -> list[str]:
    errors: list[str] = []
    n_a, n_s = len(data.alternatives), len(data.states)
    if len(data.probs) != n_s:
        errors.append(f"概率个数({len(data.probs)})与状态数({n_s})不一致")
    if abs(sum(data.probs) - 1.0) > 1e-6:
        errors.append(f"概率之和应为 1，当前为 {sum(data.probs):.6f}")
    if len(data.payoffs) != n_a:
        errors.append(f"收益矩阵行数({len(data.payoffs)})与方案数({n_a})不一致")
    else:
        for i, row in enumerate(data.payoffs):
            if len(row) != n_s:
                errors.append(f"方案 {data.alternatives[i]} 的收益列数应为 {n_s}")
            elif any(not np.isfinite(x) for x in row):
                errors.append(f"方案 {data.alternatives[i]} 的收益包含非法数值")
    return errors


def solve(data: ExpectedValueInput) -> ExpectedValueResult:
    errs = validate_shape(data)
    if errs:
        raise ValueError("；".join(errs))

    payoffs = np.asarray(data.payoffs, dtype=float)
    probs = np.asarray(data.probs, dtype=float)
    ev = payoffs @ probs
    if not np.all(np.isfinite(ev)):
        raise ValueError("收益数值过大导致计算溢出，请缩小数值范围")
    ev_rounded = [round(float(x), data.decimals) for x in ev]

    if data.sense == "min":
        best_idx = int(np.argmin(ev))
        rule = "损失期望最小"
    else:
        best_idx = int(np.argmax(ev))
        rule = "收益期望最大"

    all_equal = len(data.alternatives) > 1 and (float(ev.max() - ev.min()) <= 1e-12)
    expectations = {a: ev_rounded[i] for i, a in enumerate(data.alternatives)}
    best = "" if all_equal else data.alternatives[best_idx]
    best_value = ev_rounded[best_idx]

    # 分步展示（模板插值，供前端 panel / 数字人 speak）
    lines_calc = []
    for i, alt in enumerate(data.alternatives):
        parts = [
            f"{data.payoffs[i][j]}×{data.probs[j]}" for j in range(len(data.states))
        ]
        lines_calc.append(f"E({alt}) = {' + '.join(parts)} = {ev_rounded[i]}")

    steps = [
        {
            "id": 1,
            "name": "列出方案、状态与概率",
            "values": {
                "alternatives": data.alternatives,
                "states": data.states,
                "probs": data.probs,
            },
        },
        {
            "id": 2,
            "name": "计算各方案期望值",
            "values": {"expectations": expectations, "formulas": lines_calc},
        },
        {
            "id": 3,
            "name": f"按「{rule}」选择最优方案",
            "values": {"best": best, "best_value": best_value},
        },
    ]

    panel = [
        "## 期望值准则 · 求解过程",
        "",
        "### 步骤 1：已知条件",
        f"- 方案：{', '.join(data.alternatives)}",
        f"- 状态：{', '.join(data.states)}",
        f"- 概率：{', '.join(str(p) for p in data.probs)}",
        "",
        "### 步骤 2：各方案期望值",
        *[f"- {x}" for x in lines_calc],
        "",
        "### 步骤 3：决策",
        f"- 决策规则：{rule}",
        (
            f"- **各方案期望值完全相同（{best_value}），无差异，无法确定唯一最优方案。**"
            if all_equal
            else f"- **最优方案：{best}（期望值 {best_value}）**"
        ),
        "",
        "> 数值由程序计算，不依赖大模型。",
    ]

    speak = [
        "下面用期望值准则求解。",
        "第一步，确认各方案在不同自然状态下的收益，以及各状态概率。",
        "第二步，用收益乘以对应概率再求和，得到每个方案的期望值。"
        + "；".join(f"{k}为{v}" for k, v in expectations.items())
        + "。",
        (
            f"第三步，各方案期望值均为{best_value}，无差异，无法确定唯一最优方案。"
            if all_equal
            else f"第三步，按{rule}，选择方案{best}，其期望值为{best_value}。"
        ),
    ]

    return ExpectedValueResult(
        expectations=expectations,
        best=best,
        best_value=best_value,
        all_equal=all_equal,
        steps=steps,
        panel_markdown="\n".join(panel),
        speak_lines=speak,
    )
