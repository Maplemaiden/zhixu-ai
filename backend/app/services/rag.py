"""简易知识检索：支持中文词片/n-gram + 标题加权 + 课程专名定向加权。"""
from __future__ import annotations

import re
from pathlib import Path

from app.config import get_settings

_CHUNKS: list[dict] | None = None

_STOP_PHRASES = (
    "怎么区分",
    "有什么区别",
    "有什么关系",
    "怎么理解",
    "怎么用",
    "是什么",
    "有哪些",
    "为什么",
    "什么情况",
    "什么问题",
    "适合什么",
    "指的是什么",
    "分别指什么",
    "分别是什么",
    "怎么算",
    "如何理解",
    "如何区分",
    "请问",
    "讲讲",
    "一下",
    "一个小例子",
)


def _split_markdown(text: str, source: str) -> list[dict]:
    parts = re.split(r"\n(?=#{1,3} )", text)
    chunks = []
    for i, p in enumerate(parts):
        p = p.strip()
        if len(p) < 40:
            continue
        raw_first = p.splitlines()[0]
        clean_title = re.sub(r"^#{1,6}\s*", "", raw_first).strip()[:80]
        chunks.append(
            {
                "id": f"{source}-{i}",
                "title": clean_title,
                "text": p,
                "source": source,
            }
        )
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
            chunks.extend(_split_markdown(path.read_text(encoding="utf-8-sig"), path.name))
    _CHUNKS = chunks
    return chunks


def _extract_terms(query: str) -> list[str]:
    cleaned = query
    for phrase in _STOP_PHRASES:
        cleaned = cleaned.replace(phrase, " ")

    terms: list[str] = []
    seen: set[str] = set()

    def _add(tok: str) -> None:
        tok = tok.strip()
        if len(tok) < 2 or tok in seen:
            return
        seen.add(tok)
        terms.append(tok)

    # 英文/缩写/符号词（如 AHP, DEA, TOPSIS, M/M/1, EVPI, CR）
    for m in re.findall(r"[A-Za-z][A-Za-z0-9/_+-]*", query):
        _add(m)

    # 中文连续片段：既保留完整短词（<=5字），又提取 2-gram / 3-gram 克服无空格长句
    for seg in re.findall(r"[\u4e00-\u9fff]{2,}", cleaned):
        if len(seg) <= 5:
            _add(seg)
        for n in (3, 2):
            if len(seg) >= n:
                for i in range(len(seg) - n + 1):
                    _add(seg[i : i + n])
    return terms


def retrieve(query: str, top_k: int = 4) -> list[dict]:
    chunks = load_chunks()
    if not chunks:
        return []
    q_terms = _extract_terms(query)
    q_upper = query.upper()
    scored: list[tuple[float, dict]] = []

    is_ev_core = (
        "期望值准则" in query
        or "期望损益" in query
        or (
            "期望值" in query
            and "等概率" not in query
            and "拉普拉斯" not in query
            and "不确定型" not in query
        )
    )
    is_risk_vs_unc = "风险型" in query and "不确定" in query

    for c in chunks:
        score = 0.0
        text = c["text"]
        title = c["title"]
        source = c["source"]
        text_upper = text.upper()
        title_upper = title.upper()

        for t in q_terms:
            t_up = t.upper()
            weight = 1.6 if len(t) >= 3 else 1.0
            if t_up in title_upper:
                score += 3.5 * weight
            if t_up in text_upper:
                score += weight * (1.0 + 0.25 * min(text_upper.count(t_up), 5))

        if is_ev_core:
            if "期望值_第二讲" in source:
                score += 12
                if "期望值准则" in title or "期望值" in title:
                    score += 8
            elif "不确定型" in source:
                score *= 0.35

        if is_risk_vs_unc:
            if "概述_第一讲" in source and ("分类" in title or "风险型" in text):
                score += 10
            elif "期望值_第二讲" in source or "不确定型" in source:
                score += 4

        if "期望" in query and "期望" in text:
            score += 2
        if "风险" in query and "风险" in text:
            score += 2
        if ("决策树" in query or "剪枝" in query) and "决策树" in text:
            score += 6
        if ("贝叶斯" in query or "后验" in query or "先验" in query or "EVPI" in q_upper) and (
            "贝叶斯" in text or "后验" in text or "EVPI" in text_upper
        ):
            score += 6
        if (
            "不确定" in query
            or "乐观" in query
            or "悲观" in query
            or "后悔" in query
            or "折中" in query
            or "赫威斯" in query
            or "拉普拉斯" in query
            or "等概率" in query
        ) and ("不确定" in source or "乐观" in text or "悲观" in text or "后悔" in text):
            score += 6
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
            or "概述" in source
        ):
            score += 6

        boosts = [
            (("效用并合", "目标准则体系", "距离规则", "效用"), ("效用", "目标准则", "并合"), "效用"),
            (("DEA", "数据包络", "DMU", "相对有效"), ("DEA", "数据包络", "决策单元", "相对有效"), "DEA"),
            (("目标规划", "偏差变量", "优先因子"), ("目标规划", "偏差", "优先"), "目标规划"),
            (("AHP", "层次分析", "判断矩阵", "一致性"), ("层次分析", "判断矩阵", "一致性", "AHP"), "AHP"),
            (("马尔可夫", "转移矩阵", "无后效", "平稳分布"), ("马尔可夫", "转移", "无后效"), "马尔可夫"),
            (("离散事件", "仿真时钟", "事件表", "排队", "M/M/1"), ("离散事件", "仿真", "事件", "排队"), "离散"),
            (("多属性", "决策矩阵", "TOPSIS", "预处理", "加权和", "加权积", "ELECTRE", "PROMETHEE"), ("多属性", "决策矩阵", "预处理", "TOPSIS", "加权"), "多属性"),
        ]
        for qkeys, tkeys, src_hint in boosts:
            if any(k.upper() in q_upper for k in qkeys) and (
                any(k.upper() in text_upper for k in tkeys) or src_hint in source
            ):
                score += 6

        if title in {"课程信息", "整理说明"} or "附录" in title or "图片索引" in title:
            score *= 0.15

        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]
