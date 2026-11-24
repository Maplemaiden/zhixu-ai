/** 方法推荐：收集全部关键词命中，再按课程判定消歧，而不是只取第一条。 */

export const METHOD_TITLE = {
  overview_scope: "课程定位与广义决策",
  overview_elements: "决策六要素",
  overview_types: "决策分类与分流",
  overview_process: "五原则与五步骤",
  decision_overview: "决策要素与决策过程",
  uncertainty_setup: "不确定型适用条件",
  uncertainty_criteria: "不确定型五准则",
  bayes: "贝叶斯决策分析",
  decision_tree: "决策树分析法",
  expected_value: "期望值准则",
  utility_system: "目标准则体系",
  utility_combine: "多维效用并合规则",
  dea_motivation: "为何需要 DEA",
  dea: "DMU 与相对有效性",
  gp_deviations: "目标规划与偏差变量",
  goal_programming: "加权与优先目标规划",
  ahp_structure: "递阶层次结构",
  ahp: "判断矩阵与一致性",
  markov_property: "马尔可夫性与链",
  markov: "转移矩阵与分布预测",
  madm9_prep: "第九讲·预处理补充与初筛",
  madm9_weight: "第九讲·定权",
  madm9_scoring: "第九讲·加权与TOPSIS",
  madm9_outranking: "第九讲·ELECTRE/PROMETHEE",
  sim_basics: "仿真动机与八要素",
  discrete_sim: "九大部件与排队库存",
  madm_matrix: "决策矩阵引入",
  madm_preprocess: "属性预处理",
  madm: "多属性综合排序概要",
};

const RULES = [
  {
    id: "ahp",
    reason: "涉及递阶层次、两两比较判断矩阵或一致性检验，适合层次分析法 AHP。",
    tests: [
      ["层次分析", /层次分析|AHP|ahp/],
      ["判断矩阵", /判断矩阵/],
      ["一致性检验", /一致性检验|一致性比率|\bCR\b|\bCI\b/],
      ["1-9标度", /1\s*[-–]\s*9\s*标度|九标度/],
    ],
  },
  {
    id: "dea",
    reason: "评价同类单元相对效率、多投入多产出且量纲不便直接加总，适合 DEA。",
    tests: [
      ["DEA", /\bDEA\b|数据包络/],
      ["决策单元", /决策单元|\bDMU\b/],
      ["相对有效", /相对有效/],
      ["投入产出", /投入.*产出|多投入/],
    ],
  },
  {
    id: "goal_programming",
    reason: "多目标要逼近期望水平，出现正负偏差或优先等级，适合目标规划。",
    tests: [
      ["目标规划", /目标规划/],
      ["正偏差", /正偏差|负偏差|偏差变量/],
      ["优先因子", /优先因子|优先目标/],
      ["加权目标", /加权目标规划/],
    ],
  },
  {
    id: "utility_combine",
    reason: "多目标要构造目标准则体系并用效用并合（距离/代换/加乘等），适合第四讲。",
    tests: [
      ["效用并合", /效用并合|多维效用/],
      ["目标准则体系", /目标准则体系/],
      ["距离规则", /距离规则|代换规则/],
      ["序列型多层次", /序列型多层次/],
    ],
  },
  {
    id: "markov",
    reason: "涉及无后效性、状态转移矩阵或占有率预测，适合马尔可夫一讲。",
    tests: [
      ["马尔可夫", /马尔可夫|Markov/],
      ["转移矩阵", /转移矩阵|转移概率/],
      ["无后效", /无后效/],
      ["市场占有率", /市场占有率|长期占有率/],
    ],
  },
  {
    id: "madm",
    reason: "有限方案多属性决策矩阵、属性预处理或 TOPSIS 等，适合多属性决策。",
    tests: [
      ["多属性", /多属性决策|多属性/],
      ["决策矩阵", /决策矩阵/],
      ["TOPSIS", /TOPSIS|逼近理想解/],
      ["属性预处理", /属性预处理|效益型|成本型属性/],
    ],
  },
  {
    id: "discrete_sim",
    reason: "离散事件、仿真时钟、事件表或排队库存仿真，适合第十讲。",
    tests: [
      ["离散事件", /离散事件/],
      ["仿真时钟", /仿真时钟/],
      ["事件表", /事件表/],
      ["系统仿真", /系统仿真|仿真模型/],
    ],
  },
  {
    id: "decision_overview",
    reason: "题干在问决策定义、六要素、分类、原则或五步骤等概念框架，适合先进入第一讲概述。",
    tests: [
      ["六要素", /六要素/],
      ["决策要素", /决策要素/],
      ["广义决策", /广义决策/],
      ["狭义决策", /狭义决策/],
      ["西蒙", /西蒙/],
      ["管理就是决策", /管理就是决策/],
      ["决策步骤", /决策步骤|五步骤|决策程序/],
      ["基本原则", /基本原则|信息充分|系统原则/],
      ["田忌赛马", /田忌赛马/],
      ["程序化决策", /程序化决策|非程序化/],
      ["定性决策", /定性决策|定量决策|综合决策/],
    ],
  },
  {
    id: "overview_elements",
    reason: "明确在问六要素或状态/方案区分，进入「决策六要素」知识点。",
    tests: [["六要素", /六要素/], ["自然状态", /自然状态.*方案|方案.*自然状态/]],
  },
  {
    id: "overview_types",
    reason: "在问风险型/不确定型分流或决策分类，进入分类知识点。",
    tests: [["风险型", /风险型决策/], ["不确定型决策", /不确定型决策/], ["程序化", /程序化决策/]],
  },
  {
    id: "madm9_scoring",
    reason: "第九讲教材评分法：加权和/加权积/TOPSIS。",
    tests: [["TOPSIS", /TOPSIS|逼近理想解/], ["加权积", /加权积/], ["理想解", /理想解|负理想解/]],
  },
  {
    id: "madm9_outranking",
    reason: "级别高于方法：ELECTRE 或 PROMETHEE。",
    tests: [["ELECTRE", /ELECTRE/], ["PROMETHEE", /PROMETHEE/], ["级别高于", /级别高于/]],
  },
  {
    id: "uncertainty_criteria",
    reason: "题干给出状态但没有概率，适合不确定型五准则（乐观/悲观/折中/后悔值/等概率）。",
    tests: [
      ["不确定", /不确定/],
      ["没有概率", /没有概率/],
      ["概率未知", /概率未知/],
      ["概率无从", /概率无从/],
      ["乐观准则", /乐观准则/],
      ["悲观准则", /悲观准则/],
      ["后悔值", /后悔值/],
      ["等概率", /等概率/],
    ],
  },
  {
    id: "bayes",
    reason: "已有先验，又出现调查、检测等补充信息，应先修正为后验再做期望值决策。",
    tests: [
      ["贝叶斯", /贝叶斯/],
      ["先验", /先验/],
      ["后验", /后验/],
      ["补充信息", /补充信息/],
      ["市场调查", /市场调查/],
      ["检测阳性", /检测阳性/],
      ["信息价值", /信息价值/],
    ],
  },
  {
    id: "decision_tree",
    reason: "涉及画树、多阶段或剪枝回推，优先用决策树把方案与状态摊开。",
    tests: [
      ["决策树", /决策树/],
      ["画树", /画树/],
      ["多阶段", /多阶段/],
      ["剪枝", /剪枝/],
      ["回推", /回推/],
    ],
  },
  {
    id: "expected_value",
    reason: "状态概率已知（或可估计），按风险型决策的期望值准则选优。",
    tests: [
      ["期望值", /期望值/],
      ["概率已知", /概率已知/],
      ["风险型", /风险型/],
      ["损益矩阵", /损益矩阵/],
      ["概率为", /概率为/],
    ],
  },
];

/** 课程消歧：概念框架优先；计算类里越靠前越“先判定问题类型”。 */
const TYPE_RANK = [
  "ahp",
  "dea",
  "goal_programming",
  "utility_combine",
  "markov",
  "madm",
  "discrete_sim",
  "decision_overview",
  "uncertainty_criteria",
  "bayes",
  "decision_tree",
  "expected_value",
];

function collectHits(q) {
  const hits = [];
  for (const r of RULES) {
    const matched = r.tests.filter(([, re]) => re.test(q)).map(([label]) => label);
    if (matched.length) {
      hits.push({
        methodId: r.id,
        title: METHOD_TITLE[r.id],
        reason: r.reason,
        matched,
        score: matched.length,
      });
    }
  }
  if (/概率/.test(q) && !/未知|没有|不掌握|无从/.test(q)) {
    if (!hits.some((h) => h.methodId === "expected_value")) {
      hits.push({
        methodId: "expected_value",
        title: METHOD_TITLE.expected_value,
        reason: "提到了概率且未说明未知，可按期望值准则处理。",
        matched: ["概率"],
        score: 1,
      });
    }
  }
  return hits;
}

function pickPrimary(hits, q) {
  const ids = new Set(hits.map((h) => h.methodId));
  // 没有概率 → 不确定型压过期望值/决策树
  if (ids.has("uncertainty_criteria") && /没有概率|概率未知|概率无从|不确定/.test(q)) {
    return hits.find((h) => h.methodId === "uncertainty_criteria");
  }
  // 同题里期望值经常只是树/贝叶斯的计算，不当成首选
  const typed = hits.filter((h) => h.methodId !== "expected_value");
  const pool = typed.length ? typed : hits;
  return [...pool].sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return TYPE_RANK.indexOf(a.methodId) - TYPE_RANK.indexOf(b.methodId);
  })[0];
}

export function recommendMethod(text) {
  const q = String(text || "").trim();
  if (!q) return null;

  const hits = collectHits(q);
  if (!hits.length) {
    return {
      methodId: null,
      rejected: true,
      reason: "没有识别到本课决策条件（概率、状态、调查信息、决策树等），不能推荐方法。请贴课程相关题干。",
      hits: [],
      alternatives: [],
    };
  }

  const primary = pickPrimary(hits, q);
  const alternatives = hits.filter((h) => h.methodId !== primary.methodId);
  const evNote =
    alternatives.some((h) => h.methodId === "expected_value") ||
    (primary.methodId !== "expected_value" && hits.some((h) => h.methodId === "expected_value"))
      ? "期望值在这里是后续计算步骤，不是与该方法并列的另一种首选。"
      : "";

  return {
    methodId: primary.methodId,
    rejected: false,
    reason: primary.reason,
    matched: primary.matched,
    evNote,
    hits,
    alternatives,
  };
}
