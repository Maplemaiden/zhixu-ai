"""教材讲法步骤卡：锁死讲解顺序与符号，避免通用模型串讲法。"""

from app.services.step_cards_extra import EXTRA_STEP_CARDS
from app.services.step_cards_fine import FINE_STEP_CARDS

STEP_CARDS: dict[str, dict] = {
    "decision_overview": {
        "method_id": "decision_overview",
        "title": "决策要素与决策过程",
        "chapter": "决策理论与方法概述",
        "source": "课程第一讲 / 决策分析概念·要素·分类·原则·步骤",
        "symbols": {
            "决策者": "决策主体（个体或群体）",
            "目标": "拟定与评价方案的基准",
            "方案": "可控的行动备选",
            "自然状态": "不可控但可预见的客观环境",
            "结果": "方案×状态下的后果",
            "准则": "选优的价值标准",
        },
        "intro_story": [
            "本课研究如何把管理中的选择变成可分析、可比较的决策过程；取广义理解（发现问题到实施反馈）。",
            "第一讲按知识点分开学：定位 → 六要素 → 分类分流 → 五步骤；口诀只在对应知识点里记。",
        ],
        "steps": [
            "先理解课程定位：广义决策 = 决策分析全过程（西蒙）",
            "识别六要素：决策者、目标、方案、自然状态、结果、准则",
            "区分状态（不可控可预见）与方案（可控）——建模第一步",
            "按自然状态分流：确定型 / 风险型（有概率）/ 不确定型（无概率）",
            "按五原则与五步骤推进，并理解定性、定量与综合方法",
        ],
        "step_details": [
            {
                "title": "课程定位：广义决策",
                "points": [
                    "狭义：只从备选方案里做一次最佳选择。",
                    "广义：发现问题 → 提出问题 → 解决问题全过程。",
                    "本课取广义；理论来源是西蒙“管理就是决策”。",
                ],
            },
            {
                "title": "六要素（记忆口诀）",
                "points": [
                    "决策者 → 目标 → 方案 → 自然状态 → 结果 → 准则。",
                    "目标可以是多目标（如蛋多用、又省事）。",
                    "准则与决策者价值取向、风险偏好有关。",
                ],
            },
            {
                "title": "状态 vs 方案",
                "points": [
                    "自然状态：无法控制但可以预见（如蛋好/坏、销路好/差）。",
                    "行动方案：决策者可控的措施。",
                    "分不清这两项，后面的损益矩阵行列就会建反。",
                ],
            },
            {
                "title": "最重要分流：有没有概率",
                "points": [
                    "确定型：每方案一种结果，条件确知。",
                    "风险型：多种结果，概率可预测 → 第二讲期望值等。",
                    "不确定型：多种结果，概率完全未知 → 第三讲五准则。",
                ],
            },
            {
                "title": "五原则 · 五步骤 · 方法类型",
                "points": [
                    "五原则：信息充分、系统、科学、可行、反馈。",
                    "五步骤：形成问题 → 定目标（针对性/准确性/约束性）→ 拟方案 → 选方案 → 实施反馈。",
                    "定性灵活但主观；定量可求优但难覆盖全部定性因素；复杂问题宜综合决策。",
                ],
            },
        ],
        "speak_intro": "欢迎来到第一讲。先定课程定位，再按知识点分别学六要素、分类和五步骤。",
        "formula_latex": "",
        "has_compute": False,
        "compute_note": "本讲是概念框架：导入讲清课程定位，步骤段展开术语，案例段拆教材例，不调用数值 Solver。",
    },
    "expected_value": {
        "method_id": "expected_value",
        "title": "期望值准则",
        "chapter": "风险型决策",
        "source": "课程第二讲 / 教材风险型决策·期望值准则",
        "symbols": {"E": "期望损益值", "θ": "自然状态", "p": "状态概率", "a": "行动方案"},
        "intro_story": [
            "风险型决策：状态概率已知时，用各方案期望损益选优。",
        ],
        "steps": [
            "确认决策目标（收益最大或损失最小）",
            "列出方案、自然状态、概率与损益矩阵",
            "计算各方案期望值 E(a_i)=Σ payoffs_ij × p_j",
            "按期望值最优规则选出满意方案",
            "必要时做灵敏度讨论（增强项）",
        ],
        "speak_intro": "我们按课程中的期望值准则，分步来看这道风险型决策题。",
        "formula_latex": r"E(a_i)=\sum_j payoffs_{ij}\times p_j",
        "has_compute": True,
        "compute_kind": "expected_value",
    },
    "decision_tree": {
        "method_id": "decision_tree",
        "title": "决策树分析法",
        "chapter": "风险型决策",
        "source": "课程第二讲 / 决策树分析法",
        "symbols": {"□": "决策点", "○": "状态节点", "E": "节点期望值"},
        "intro_story": [
            "决策树把方案、状态、结果画开，再用期望值从右向左回推剪枝。",
        ],
        "steps": [
            "明确决策目标与可选方案、可能状态及概率",
            "从左到右绘制决策树（决策点、方案枝、状态点、概率枝、结果值）",
            "从右到左计算各状态节点期望值",
            "在决策点比较方案期望值，剪枝选出满意方案",
            "多阶段决策时按整体最优目标逐层回推",
        ],
        "speak_intro": "决策树用图形把方案、状态和结果摊开，再用期望值从右向左回推决策。",
        "formula_latex": r"E(\text{状态点})=\sum_k \text{结果}_k\times p_k",
        "has_compute": True,
        "compute_kind": "expected_value",
        "compute_note": "单阶段决策树回推本质仍是期望值计算；本课先用等价收益表验算。",
    },
    "bayes": {
        "method_id": "bayes",
        "title": "贝叶斯决策分析",
        "chapter": "风险型决策",
        "source": "课程第二讲 / 贝叶斯决策分析",
        "symbols": {"P(θ)": "先验概率", "P(θ|I)": "后验概率", "I": "补充信息"},
        "intro_story": [
            "贝叶斯决策：用新信息把先验修正为后验，再按后验做期望值决策。",
        ],
        "steps": [
            "给出状态的先验概率与各方案条件结果",
            "通过调查等方式获得与状态有关的补充信息",
            "用贝叶斯公式把先验概率修正为后验概率",
            "用后验概率计算各方案期望值并选优",
            "必要时比较信息价值与调查成本（增强项）",
        ],
        "speak_intro": "贝叶斯决策的关键，是用新信息修正先验概率，再按后验分布做期望值决策。",
        "formula_latex": r"P(\theta\mid I)=\dfrac{P(I\mid\theta)\,P(\theta)}{\sum_{\theta'} P(I\mid\theta')\,P(\theta')}",
        "has_compute": True,
        "compute_kind": "expected_value",
        "compute_note": "后验概率确定后，选型计算回到期望值准则。",
    },
    "uncertainty_criteria": {
        "method_id": "uncertainty_criteria",
        "title": "不确定型决策五大准则",
        "chapter": "不确定型决策",
        "source": "课程第三讲 / 不确定型决策分析",
        "symbols": {"α": "折中系数", "R": "后悔值"},
        "intro_story": [
            "不确定型无概率，用乐观/悲观/折中/后悔值/等概率五准则选方案；准则不同结果可能不同。",
        ],
        "steps": [
            "确认：状态可知但概率未知，且有收益（损失）表",
            "按决策者态度选择准则：乐观 / 悲观 / 折中 / 后悔值 / 等概率",
            "对每一方案计算该准则下的决策指标",
            "比较指标选出满意方案",
            "强调：不同准则可能得到不同方案，体现主观风险态度",
        ],
        "speak_intro": "不确定型决策没有概率，只能借助乐观、悲观、折中、后悔值和等概率等准则来选择。",
        "formula_latex": r"\text{乐观}\max_i\max_j;\ \text{悲观}\max_i\min_j;\ \text{等概率}\frac{1}{n}\sum_j;\ \text{后悔}\min_i\max_j R_{ij}",
        "has_compute": True,
        "compute_kind": "uncertainty",
    },
}

# 第四～十一讲概念加厚卡 + 讲内细分知识点
STEP_CARDS.update(EXTRA_STEP_CARDS)
STEP_CARDS.update(FINE_STEP_CARDS)


SECTION_LABELS = {
    0: "讲解",
    1: "做题答疑",
}


def format_card_for_prompt(card: dict) -> str:
    symbols = card.get("symbols") or {}
    symbol_lines = "\n".join(f"- {k}：{v}" for k, v in symbols.items()) or "- （无）"
    steps = card.get("steps") or []
    step_lines = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps)) or "- （无）"
    details = card.get("step_details") or []
    detail_lines = []
    for i, d in enumerate(details):
        pts = "；".join(d.get("points") or [])
        detail_lines.append(f"{i+1}. {d.get('title', '')}：{pts}")
    detail_block = "\n".join(detail_lines)
    intro = card.get("intro_story") or []
    intro_block = "\n".join(f"- {s}" for s in intro)
    formula = card.get("formula_latex") or ""
    formula_line = (
        f"标准公式 LaTeX 模板：${formula}$"
        if formula
        else "标准公式：本知识点以讲法与概念为主；请使用步骤卡符号与教案位置表述，勿另造记号。"
    )
    parts = [
        f"方法：{card.get('title')}（{card.get('chapter')}）",
        f"教材来源：{card.get('source')}",
        f"符号表（必须使用，禁止另造记号）：\n{symbol_lines}",
        f"标准步骤：\n{step_lines}",
        formula_line,
    ]
    if intro_block:
        parts.insert(2, f"导入简述：\n{intro_block}")
    if detail_block:
        parts.append(f"步骤展开要点：\n{detail_block}")
    return "\n".join(parts)


def get_step_card(method_id: str) -> dict | None:
    return STEP_CARDS.get(method_id)


def list_method_ids() -> list[str]:
    return list(STEP_CARDS.keys())
