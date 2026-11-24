"""规则筛空时的轻量分类：只判断是否本课 + 四类方法枚举。"""
from __future__ import annotations

import json
import re

from app.services import llm
from app.services.step_cards import list_method_ids

ALLOWED = set(list_method_ids())

SYSTEM = """你是《决策理论与方法》课程助教。任务：判断学生题干是否属于本课，并归入已开放的方法。
只输出一个 JSON 对象，不要 Markdown，不要额外文字。
字段：
- in_course: boolean  是否属于本课决策问题
- method_id: string|null  必须是已开放 method_id 之一，否则 null
  可选：decision_overview, expected_value, decision_tree, bayes, uncertainty_criteria,
  utility_combine, dea, goal_programming, ahp, markov, discrete_sim, madm
- reason: string  一两句中文，说明判定依据
- confidence: high | medium | low

判定要点：
- 古诗、闲聊、编程、其他学科、无决策要素 → in_course=false, method_id=null
- 问决策定义/西蒙/六要素/分类/五原则/五步骤 → decision_overview
- 状态概率已知、单阶段选方案 → expected_value
- 画树/多阶段/剪枝回推 → decision_tree
- 先验+调查/检测修正 → bayes
- 有状态无概率 → uncertainty_criteria
- 效用并合/目标准则体系/距离规则并合 → utility_combine
- DEA/数据包络/DMU/相对有效 → dea
- 目标规划/正负偏差/优先因子 → goal_programming
- AHP/层次分析/判断矩阵/一致性 CR → ahp
- 马尔可夫/转移矩阵/无后效性 → markov
- 离散事件仿真/仿真时钟/事件表 → discrete_sim
- 多属性/决策矩阵/TOPSIS/属性预处理 → madm
不要编造题干里没有的条件。"""


def _parse(text: str) -> dict | None:
    raw = (text or "").strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def classify_question(question: str) -> dict:
    if not llm.available():
        return {
            "in_course": False,
            "method_id": None,
            "reason": "规则未命中，且当前未配置大模型，无法做课程范畴识别。请改用课程关键词描述条件。",
            "confidence": "low",
            "source": "unavailable",
        }

    try:
        raw = llm.chat(
            [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"学生题干：{question.strip()}"},
            ],
            temperature=0,
        )
    except Exception:
        return {
            "in_course": False,
            "method_id": None,
            "reason": "规则未命中，模型接口暂时不可用，因此没有跳转章节。请改用课程关键词，或稍后再试。",
            "confidence": "low",
            "source": "error",
        }
    data = _parse(raw) or {}
    in_course = bool(data.get("in_course"))
    method_id = data.get("method_id")
    if method_id not in ALLOWED:
        method_id = None
    confidence = data.get("confidence") if data.get("confidence") in {"high", "medium", "low"} else "low"
    reason = str(data.get("reason") or "").strip()
    if not reason:
        reason = (
            "模型未能给出明确分类。"
            if in_course
            else "未识别为本课决策问题。"
        )
    return {
        "in_course": in_course,
        "method_id": method_id,
        "reason": reason,
        "confidence": confidence,
        "source": "llm",
    }
