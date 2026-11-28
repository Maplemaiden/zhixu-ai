"""多属性决策：加权和、加权积、TOPSIS。纯程序计算，不依赖大模型。"""
from __future__ import annotations

from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field, field_validator

Method = Literal["weighted_sum", "weighted_product", "topsis"]
AttrType = Literal["benefit", "cost", "interval"]

METHOD_NAMES = {
    "weighted_sum": "加权和法",
    "weighted_product": "加权积法",
    "topsis": "TOPSIS（逼近理想解）",
}


class IntervalBounds(BaseModel):
    best_low: float
    best_high: float
    tol_low: float
    tol_high: float


class MadmInput(BaseModel):
    alternatives: list[str] = Field(..., min_length=1)
    attributes: list[str] = Field(..., min_length=1)
    types: list[AttrType]
    matrix: list[list[float]] = Field(..., description="决策矩阵 [方案][属性]")
    weights: list[float]
    method: Method = "topsis"
    interval: dict[str, IntervalBounds] = Field(default_factory=dict)
    decimals: int = 4

    @field_validator("weights")
    @classmethod
    def weights_nonneg(cls, v: list[float]) -> list[float]:
        if any(w < 0 for w in v):
            raise ValueError("权重不能为负")
        return v


class MadmResult(BaseModel):
    method: str
    method_name: str
    scores: dict[str, float]
    ranking: list[str]
    best: str
    best_value: float
    all_equal: bool = False
    steps: list[dict[str, Any]]
    panel_markdown: str
    speak_lines: list[str]


def _validate(data: MadmInput) -> None:
    n_a, n_c = len(data.alternatives), len(data.attributes)
    if len(data.types) != n_c:
        raise ValueError("属性类型个数与属性数不一致")
    if len(data.weights) != n_c:
        raise ValueError("权重个数与属性数不一致")
    if abs(sum(data.weights) - 1.0) > 1e-6:
        raise ValueError(f"权重之和应为 1，当前为 {sum(data.weights):.6f}")
    if len(data.matrix) != n_a:
        raise ValueError("决策矩阵行数与方案数不一致")
    for i, row in enumerate(data.matrix):
        if len(row) != n_c:
            raise ValueError(f"方案 {data.alternatives[i]} 的属性列数应为 {n_c}")
    if not np.all(np.isfinite(np.asarray(data.weights, dtype=float))):
        raise ValueError("权重包含非法数值")
    if not np.all(np.isfinite(np.asarray(data.matrix, dtype=float))):
        raise ValueError("决策矩阵包含非法数值")
    for j, t in enumerate(data.types):
        if t == "interval":
            name = data.attributes[j]
            b = data.interval.get(name)
            if not b:
                raise ValueError(f"区间型属性「{name}」缺少最优/容忍区间")
            if not (b.tol_low < b.best_low <= b.best_high < b.tol_high):
                raise ValueError(f"属性「{name}」的区间应满足 容忍下限 < 最优下限 ≤ 最优上限 < 容忍上限")


def _interval_transform(y: float, b: IntervalBounds) -> float:
    """教案 §2.2（3）：最优值为给定区间的变换。"""
    y0, ys, yp, ypp = b.best_low, b.best_high, b.tol_low, b.tol_high
    if yp < y < y0:
        return 1.0 - (y0 - y) / (y0 - yp)
    if y0 <= y <= ys:
        return 1.0
    if ys < y < ypp:
        return 1.0 - (y - ys) / (ypp - ys)
    return 0.0


def _apply_interval(Y: np.ndarray, data: MadmInput) -> tuple[np.ndarray, list[str]]:
    """区间型先变成越大越好的 [0,1]，后续按效益型处理。"""
    out = Y.astype(float).copy()
    types = list(data.types)
    for j, t in enumerate(data.types):
        if t != "interval":
            continue
        b = data.interval[data.attributes[j]]
        for i in range(out.shape[0]):
            out[i, j] = _interval_transform(float(out[i, j]), b)
        types[j] = "benefit"
    return out, types


def _minmax(Y: np.ndarray, types: list[str]) -> np.ndarray:
    """标准 0-1 变换。列内全相等时记为 1；极端大数先缩放防差值溢出。"""
    z = np.zeros_like(Y, dtype=float)
    for j, t in enumerate(types):
        col = Y[:, j]
        lo, hi = float(col.min()), float(col.max())
        span = hi - lo
        if not np.isfinite(span):
            scale = max(abs(lo), abs(hi))
            col_s = col / scale
            lo_s, hi_s = lo / scale, hi / scale
            span_s = hi_s - lo_s
            if span_s <= 1e-15:
                z[:, j] = 1.0
            elif t == "cost":
                z[:, j] = (hi_s - col_s) / span_s
            else:
                z[:, j] = (col_s - lo_s) / span_s
            continue
        if span <= 1e-15:
            z[:, j] = 1.0
            continue
        if t == "cost":
            z[:, j] = (hi - col) / span
        else:
            z[:, j] = (col - lo) / span
    return z


def _linear(Y: np.ndarray, types: list[str]) -> np.ndarray:
    """线性变换：效益 y/ymax；成本 ymin/y（不用 1−y/ymax，避免最差方案直接为 0）。"""
    z = np.zeros_like(Y, dtype=float)
    for j, t in enumerate(types):
        col = Y[:, j]
        if t == "cost":
            lo = float(col.min())
            if lo <= 0 or np.any(col <= 0):
                raise ValueError("加权积法的成本型属性须全为正，才能用 ymin/y")
            z[:, j] = lo / col
        else:
            if np.any(col < 0):
                raise ValueError("加权积法的效益型属性不能为负数")
            hi = float(col.max())
            if hi <= 0:
                raise ValueError("效益型属性列最大值为 0，无法做线性变换")
            z[:, j] = col / hi
    return z


def _vector_norm(Y: np.ndarray) -> np.ndarray:
    """向量规范化：逐列先按最大绝对值缩放再求 L2 范数，防止 1e200 等超大值平方溢出归零。"""
    out = np.zeros_like(Y, dtype=float)
    for j in range(Y.shape[1]):
        col = Y[:, j]
        scale = float(np.max(np.abs(col)))
        if scale <= 1e-300:
            continue
        scaled = col / scale
        norm = float(np.linalg.norm(scaled))
        if norm > 0 and np.isfinite(norm):
            out[:, j] = scaled / norm
    return out


def _rank(alts: list[str], scores: dict[str, float]) -> list[str]:
    return sorted(alts, key=lambda a: (-scores[a], alts.index(a)))


def solve(data: MadmInput) -> MadmResult:
    _validate(data)
    Y_raw = np.asarray(data.matrix, dtype=float)
    Y, types = _apply_interval(Y_raw, data)
    alts = data.alternatives
    attrs = data.attributes
    w = np.asarray(data.weights, dtype=float)
    d = data.decimals
    method_name = METHOD_NAMES[data.method]
    steps: list[dict[str, Any]] = []
    detail: list[str] = []

    if data.method == "topsis":
        z = _vector_norm(Y)
        x = z * w
        ideal = np.zeros(len(attrs))
        nadir = np.zeros(len(attrs))
        for j, t in enumerate(types):
            col = x[:, j]
            if t == "cost":
                ideal[j] = float(col.min())
                nadir[j] = float(col.max())
            else:
                ideal[j] = float(col.max())
                nadir[j] = float(col.min())
        d_pos = np.sqrt(((x - ideal) ** 2).sum(axis=1))
        d_neg = np.sqrt(((x - nadir) ** 2).sum(axis=1))
        denom = d_pos + d_neg
        c = np.divide(d_neg, denom, out=np.zeros_like(d_neg), where=denom > 1e-15)
        raw_scores = {alts[i]: float(c[i]) for i in range(len(alts))}
        scores = {k: round(v, d) for k, v in raw_scores.items()}
        steps = [
            {"id": 1, "name": "向量规范化", "values": {"Z": np.round(z, d).tolist()}},
            {"id": 2, "name": "加权规范矩阵", "values": {"X": np.round(x, d).tolist()}},
            {
                "id": 3,
                "name": "正负理想解",
                "values": {
                    "positive": [round(float(v), d) for v in ideal],
                    "negative": [round(float(v), d) for v in nadir],
                },
            },
            {
                "id": 4,
                "name": "距离与贴近度",
                "values": {
                    "d_star": [round(float(v), d) for v in d_pos],
                    "d_0": [round(float(v), d) for v in d_neg],
                    "c_star": scores,
                },
            },
        ]
        detail = [
            f"{alts[i]}：$d^*$={round(float(d_pos[i]), d)}，$d^0$={round(float(d_neg[i]), d)}，$c^*$={scores[alts[i]]}"
            for i in range(len(alts))
        ]
        formula_note = (
            "TOPSIS：先向量规范化 $z_{ij}=y_{ij}/\\sqrt{\\sum_i y_{ij}^2}$，再 $x_{ij}=w_j z_{ij}$；"
            "效益型正理想取列最大、负理想取列最小，成本型相反；"
            "$c_i^*=d_i^0/(d_i^0+d_i^*)$，越大越好。"
        )

    elif data.method == "weighted_sum":
        z = _minmax(Y, types)
        u = z @ w
        raw_scores = {alts[i]: float(u[i]) for i in range(len(alts))}
        scores = {k: round(v, d) for k, v in raw_scores.items()}
        steps = [
            {"id": 1, "name": "标准 0-1 变换", "values": {"Z": np.round(z, d).tolist()}},
            {"id": 2, "name": "加权和 $u_i=\\sum w_j z_{ij}$", "values": {"scores": scores}},
        ]
        detail = [f"{a}：$u$={scores[a]}" for a in alts]
        formula_note = (
            "加权和法：先做标准 0-1 变换，再 $u_i=\\sum_j w_j z_{ij}$。"
            "假设属性价值独立且可完全补偿。"
        )

    else:
        z = _linear(Y, types)
        # z^w 逐列连乘：当 w_j > 0 且 z_{ij} <= 0 时严格得 0（体现不可代偿性）；w_j == 0 时该属性因子为 1
        u = np.ones(len(alts), dtype=float)
        for j in range(len(attrs)):
            wj = float(w[j])
            if wj <= 0:
                continue
            col_z = z[:, j]
            u *= np.where(col_z <= 0, 0.0, np.power(np.maximum(col_z, 1e-300), wj))
        raw_scores = {alts[i]: float(u[i]) for i in range(len(alts))}
        scores = {k: round(v, d) for k, v in raw_scores.items()}
        steps = [
            {"id": 1, "name": "线性变换（成本用 $y^{min}/y$）", "values": {"Z": np.round(z, d).tolist()}},
            {"id": 2, "name": "加权积 $u_i=\\prod z_{ij}^{w_j}$", "values": {"scores": scores}},
        ]
        detail = [f"{a}：$u$={scores[a]}" for a in alts]
        formula_note = (
            "加权积法：线性变换后 $u_i=\\prod_j z_{ij}^{w_j}$。"
            "假设属性之间不可代偿；某一属性为 0 则综合值为 0。"
        )

    ranking = _rank(alts, raw_scores)
    raw_vals = list(raw_scores.values())
    all_equal = len(alts) > 1 and (max(raw_vals) - min(raw_vals) <= 1e-12)
    best = "" if all_equal else ranking[0]
    best_value = scores[ranking[0]]
    type_labels = {"benefit": "效益", "cost": "成本", "interval": "区间"}
    type_line = "；".join(
        f"{attrs[j]}（{type_labels.get(data.types[j], data.types[j])}，w={data.weights[j]}）"
        for j in range(len(attrs))
    )
    rank_text = " = ".join(ranking) if all_equal else " ≻ ".join(ranking)

    panel = [
        f"## {method_name} · 求解过程",
        "",
        "### 已知",
        f"- 方案：{', '.join(alts)}",
        f"- 属性：{type_line}",
        f"- {formula_note}",
        "",
        "### 各方案得分",
        *[f"- {line}" for line in detail],
        "",
        "### 排序",
        *(
            [
                f"- **{rank_text}**",
                f"- **各方案无差异（得分均为 {best_value}），无法排定唯一最优方案。**",
            ]
            if all_equal
            else [
                f"- **{rank_text}**",
                f"- **最优方案：{best}（{best_value}）**",
            ]
        ),
        "",
        "> 数值由程序计算，不依赖大模型。",
    ]

    speak = [
        f"下面用{method_name}排序。",
        f"属性与权重：{type_line}。",
        "各方案得分：" + "；".join(f"{k}为{v}" for k, v in scores.items()) + "。",
        (
            f"各方案得分完全相同，均为{best_value}，无差异，无法确定唯一最优方案。"
            if all_equal
            else f"由大到小为{rank_text}，最优方案是{best}。"
        ),
    ]

    return MadmResult(
        method=data.method,
        method_name=method_name,
        scores=scores,
        ranking=ranking,
        best=best,
        best_value=best_value,
        all_equal=all_equal,
        steps=steps,
        panel_markdown="\n".join(panel),
        speak_lines=speak,
    )
