"""按知识点抽取课程讲义正文，供「讲解」页展示（不是只有步骤提纲）。"""
from __future__ import annotations

from app.services import rag
from app.services.step_cards import get_step_card

# method_id → 知识文件；细知识点再用标题关键词收窄切片
METHOD_SOURCE: dict[str, str] = {
    "decision_overview": "概述_第一讲.md",
    "overview_scope": "概述_第一讲.md",
    "overview_elements": "概述_第一讲.md",
    "overview_types": "概述_第一讲.md",
    "overview_process": "概述_第一讲.md",
    "expected_value": "期望值_第二讲.md",
    "decision_tree": "期望值_第二讲.md",
    "bayes": "期望值_第二讲.md",
    "uncertainty_setup": "不确定型决策_第三讲.md",
    "uncertainty_criteria": "不确定型决策_第三讲.md",
    "utility_system": "效用并合_第四讲.md",
    "utility_combine": "效用并合_第四讲.md",
    "dea_motivation": "DEA_第五讲.md",
    "dea": "DEA_第五讲.md",
    "gp_deviations": "目标规划_第六讲.md",
    "goal_programming": "目标规划_第六讲.md",
    "ahp_structure": "AHP_第七讲.md",
    "ahp": "AHP_第七讲.md",
    "markov_property": "马尔可夫_第八讲.md",
    "markov": "马尔可夫_第八讲.md",
    "madm9_prep": "多属性决策_第九章.md",
    "madm9_weight": "多属性决策_第九章.md",
    "madm9_scoring": "多属性决策_第九章.md",
    "madm9_outranking": "多属性决策_第九章.md",
    "sim_basics": "离散事件仿真_第十讲.md",
    "discrete_sim": "离散事件仿真_第十讲.md",
    "madm_matrix": "多属性决策_第十一讲.md",
    "madm_preprocess": "多属性决策_第十一讲.md",
    "madm": "多属性决策_第十一讲.md",
}

SECTION_HINTS: dict[str, list[str]] = {
    "overview_scope": ["这门课在学什么", "为什么先学概述", "狭义决策与广义决策", "田忌赛马", "决策分析的概念"],
    "overview_elements": ["六个基本要素", "鸡蛋煎饼", "六要素"],
    "overview_types": ["分类", "按自然状态", "风险型", "不确定型", "基本原则"],
    "overview_process": ["步骤", "追踪决策", "五步骤", "定性与定量", "基本原则"],
    "expected_value": ["期望值", "风险型", "损益"],
    "decision_tree": ["决策树", "剪枝", "回推"],
    "bayes": ["贝叶斯", "先验", "后验"],
    "uncertainty_setup": ["不确定型", "适用", "无概率"],
    "uncertainty_criteria": ["乐观", "悲观", "折中", "后悔", "等概率", "五准则"],
    "utility_system": ["目标准则体系", "多层次"],
    "utility_combine": ["效用并合", "距离规则", "并合"],
    "dea_motivation": ["引例", "为何", "比率"],
    "dea": ["DEA", "DMU", "相对有效", "CCR"],
    "gp_deviations": ["偏差", "目标规划", "期望值"],
    "goal_programming": ["加权", "优先", "目标规划"],
    "ahp_structure": ["层次", "递阶", "结构"],
    "ahp": ["判断矩阵", "一致性", "CR", "特征向量"],
    "markov_property": ["无后效", "马尔可夫性", "马尔可夫链"],
    "markov": ["转移", "占有率", "预测"],
    "madm9_prep": ["预处理", "初筛", "决策矩阵"],
    "madm9_weight": ["权重", "本征", "最小二乘"],
    "madm9_scoring": ["加权和", "加权积", "TOPSIS"],
    "madm9_outranking": ["ELECTRE", "PROMETHEE", "级别高于"],
    "sim_basics": ["仿真", "八要素", "为何"],
    "discrete_sim": ["九大部件", "排队", "库存", "事件"],
    "madm_matrix": ["决策矩阵", "问题引入"],
    "madm_preprocess": ["预处理", "规范化", "非量纲"],
    "madm": ["决策矩阵", "预处理", "权重", "加权", "TOPSIS", "排序"],
}


def _score_chunk(text: str, title: str, hints: list[str]) -> float:
    blob = f"{title}\n{text}"
    score = 0.0
    for h in hints:
        if not h:
            continue
        if h in title:
            score += 8
        if h in text:
            score += 3 + min(text.count(h), 5)
    # 附录/索引类切片降权，避免挤占正文
    if "附录" in title or "图片索引" in title or "原 PPT" in title:
        score *= 0.15
    if len(text) < 120:
        score *= 0.5
    return score


def get_lesson_reading(method_id: str, limit: int = 4) -> dict:
    card = get_step_card(method_id)
    source = METHOD_SOURCE.get(method_id)
    hints = list(SECTION_HINTS.get(method_id) or [])
    if card:
        hints.append(card.get("title") or "")
        hints.extend((card.get("symbols") or {}).keys())
        for d in card.get("step_details") or []:
            if d.get("title"):
                hints.append(d["title"])

    chunks = rag.load_chunks()
    pool = [c for c in chunks if not source or c["source"] == source]
    if not pool:
        pool = chunks

    scored: list[tuple[int, float, dict]] = []
    for idx, c in enumerate(pool):
        s = _score_chunk(c["text"], c["title"], [h for h in hints if h])
        if s > 0:
            scored.append((idx, s, c))
    scored.sort(key=lambda x: x[1], reverse=True)

    top_items = scored[:limit]
    # 选中最相关的切片后，恢复其在原始教材/讲义中的先后顺序，避免小节跳号乱序
    top_items.sort(key=lambda x: x[0])
    picked = [c for _, _, c in top_items]
    if not picked and pool:
        # 该讲文件兜底：取靠前的若干切片，避免讲解页空白
        picked = pool[: min(limit, 3)]

    sections = [
        {
            "title": c["title"].lstrip("# ").strip(),
            "source": c["source"],
            "text": c["text"],
        }
        for c in picked
    ]
    return {
        "method_id": method_id,
        "source": source,
        "title": (card or {}).get("title") or method_id,
        "sections": sections,
    }
