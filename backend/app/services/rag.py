"""简易知识检索：中期先用关键词+切片，不强制 Chroma；有 embedding 后再升级。"""
from __future__ import annotations

import re
from pathlib import Path

from app.config import get_settings

_CHUNKS: list[dict] | None = None


def _split_markdown(text: str, source: str) -> list[dict]:
    parts = re.split(r"\n(?=#{1,3} )", text)
    chunks = []
    for i, p in enumerate(parts):
        p = p.strip()
        if len(p) < 40:
            continue
        title = p.splitlines()[0][:80]
        chunks.append({"id": f"{source}-{i}", "title": title, "text": p, "source": source})
    return chunks


def load_chunks(force: bool = False) -> list[dict]:
    global _CHUNKS
    if _CHUNKS is not None and not force:
        return _CHUNKS
    settings = get_settings()
    chunks: list[dict] = []
    folder: Path = settings.knowledge_dir
    if folder.exists():
        for path in sorted(folder.glob("*.md")):
            chunks.extend(_split_markdown(path.read_text(encoding="utf-8"), path.name))
    _CHUNKS = chunks
    return chunks


def retrieve(query: str, top_k: int = 4) -> list[dict]:
    chunks = load_chunks()
    if not chunks:
        return []
    q_terms = [t for t in re.split(r"\s+|，|。|、|？|\?", query) if len(t) >= 2]
    scored: list[tuple[float, dict]] = []
    for c in chunks:
        score = 0.0
        text = c["text"]
        for t in q_terms:
            if t in text:
                score += text.count(t)
        if "期望" in query and "期望" in text:
            score += 3
        if "风险" in query and "风险" in text:
            score += 2
        if ("决策树" in query or "剪枝" in query) and "决策树" in text:
            score += 4
        if ("贝叶斯" in query or "后验" in query or "先验" in query) and (
            "贝叶斯" in text or "后验" in text
        ):
            score += 4
        if ("不确定" in query or "乐观" in query or "悲观" in query or "后悔" in query) and (
            "不确定" in text or "乐观" in text or "悲观" in text
        ):
            score += 4
        if (
            "六要素" in query
            or "决策步骤" in query
            or "西蒙" in query
            or "广义决策" in query
            or "狭义决策" in query
            or "基本原则" in query
        ) and (
            "六要素" in text
            or "决策步骤" in text
            or "西蒙" in text
            or "广义" in text
            or "基本原则" in text
            or "概述" in c["source"]
        ):
            score += 4
        boosts = [
            (("效用并合", "目标准则体系", "距离规则"), ("效用", "目标准则", "并合"), "效用"),
            (("DEA", "数据包络", "DMU", "相对有效"), ("DEA", "数据包络", "决策单元", "相对有效"), "DEA"),
            (("目标规划", "偏差变量", "优先因子"), ("目标规划", "偏差", "优先"), "目标规划"),
            (("AHP", "层次分析", "判断矩阵", "一致性"), ("层次分析", "判断矩阵", "一致性", "AHP"), "AHP"),
            (("马尔可夫", "转移矩阵", "无后效"), ("马尔可夫", "转移", "无后效"), "马尔可夫"),
            (("离散事件", "仿真时钟", "事件表"), ("离散事件", "仿真", "事件"), "离散"),
            (("多属性", "决策矩阵", "TOPSIS", "预处理"), ("多属性", "决策矩阵", "预处理", "TOPSIS"), "多属性"),
        ]
        for qkeys, tkeys, src_hint in boosts:
            if any(k in query for k in qkeys) and (
                any(k in text for k in tkeys) or src_hint in c["source"]
            ):
                score += 4
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]
