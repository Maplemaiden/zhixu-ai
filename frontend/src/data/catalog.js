/** 课程目录：按「讲」分组，讲内拆细知识点（学习台入口）
 * methodId → 步骤卡/答疑
 * bankId / casesId → 可选，缺省等于 methodId（细知识点可共用整讲题库/案例）
 */

export const course = {
  name: "决策理论与方法",
  assistant: "知序 AI",
  teacher: "王军",
  blurb: "课后自主学习与答疑助教：按讲进入，再按知识点分步学、追问与练习。",
};

export const chapters = [
  {
    id: "ch1",
    title: "第一讲 · 决策理论与方法概述",
    status: "ready",
    topics: [
      {
        id: "overview_scope",
        title: "课程定位与广义决策",
        desc: "这门课学什么、为什么学；西蒙「管理就是决策」；狭义 vs 广义。",
        type: "概念",
        status: "ready",
        methodId: "overview_scope",
        bankId: "decision_overview",
        casesId: "decision_overview",
      },
      {
        id: "overview_elements",
        title: "决策六要素",
        desc: "决策者、目标、方案、自然状态、结果、准则；鸡蛋煎饼案例对齐。",
        type: "概念",
        status: "ready",
        methodId: "overview_elements",
        bankId: "decision_overview",
        casesId: "decision_overview",
      },
      {
        id: "overview_types",
        title: "决策分类与分流",
        desc: "战略/战术、程序化、确定型·风险型·不确定型（有无概率）等。",
        type: "概念",
        status: "ready",
        methodId: "overview_types",
        bankId: "decision_overview",
        casesId: "decision_overview",
      },
      {
        id: "overview_process",
        title: "五原则与五步骤",
        desc: "信息充分等五原则；形成问题→定目标→拟方案→选方案→实施反馈。",
        type: "概念",
        status: "ready",
        methodId: "overview_process",
        bankId: "decision_overview",
        casesId: "decision_overview",
      },
    ],
  },
  {
    id: "ch2",
    title: "第二讲 · 风险型决策",
    status: "ready",
    topics: [
      {
        id: "expected_value",
        title: "期望值准则",
        desc: "概率已知时按期望损益选优；含程序验算。",
        type: "计算方法",
        status: "ready",
        methodId: "expected_value",
      },
      {
        id: "decision_tree",
        title: "决策树分析法",
        desc: "决策点与状态点；从右向左回推剪枝。",
        type: "计算方法",
        status: "ready",
        methodId: "decision_tree",
      },
      {
        id: "bayes",
        title: "贝叶斯决策分析",
        desc: "先验→后验修正，再按后验期望决策。",
        type: "计算方法",
        status: "ready",
        methodId: "bayes",
      },
    ],
  },
  {
    id: "ch3",
    title: "第三讲 · 不确定型决策分析",
    status: "ready",
    topics: [
      {
        id: "uncertainty_setup",
        title: "不确定型适用条件",
        desc: "状态可知但概率未知；与风险型的唯一差别。",
        type: "概念",
        status: "ready",
        methodId: "uncertainty_setup",
        bankId: "uncertainty_criteria",
        casesId: "uncertainty_criteria",
      },
      {
        id: "uncertainty_criteria",
        title: "不确定型五大准则",
        desc: "乐观、悲观、折中、后悔值、等概率；含程序验算。",
        type: "计算方法",
        status: "ready",
        methodId: "uncertainty_criteria",
      },
    ],
  },
  {
    id: "ch4",
    title: "第四讲 · 多维效用并合模型",
    status: "ready",
    topics: [
      {
        id: "utility_system",
        title: "目标准则体系",
        desc: "为何多目标；系统性/可比性/可操作性；三种层次结构。",
        type: "概念",
        status: "ready",
        methodId: "utility_system",
        bankId: "utility_combine",
        casesId: "utility_combine",
      },
      {
        id: "utility_combine",
        title: "多维效用并合规则",
        desc: "去量纲效用；由下而上并合；距离/代换/加/乘/混合规则。",
        type: "概念",
        status: "ready",
        methodId: "utility_combine",
      },
    ],
  },
  {
    id: "ch5",
    title: "第五讲 · 数据包络分析",
    status: "ready",
    topics: [
      {
        id: "dea_motivation",
        title: "为何需要 DEA",
        desc: "四引例：从比率比较到量纲不同无法加总。",
        type: "概念",
        status: "ready",
        methodId: "dea_motivation",
        bankId: "dea",
        casesId: "dea",
      },
      {
        id: "dea",
        title: "DMU 与相对有效性",
        desc: "决策单元、投入产出、相对有效（DEA有效）思想。",
        type: "计算方法",
        status: "ready",
        methodId: "dea",
      },
    ],
  },
  {
    id: "ch6",
    title: "第六讲 · 多目标线性规划",
    status: "ready",
    topics: [
      {
        id: "gp_deviations",
        title: "目标规划思想与偏差变量",
        desc: "逼近期望；正负偏差 d⁻/d⁺；线性范围。",
        type: "概念",
        status: "ready",
        methodId: "gp_deviations",
        bankId: "goal_programming",
        casesId: "goal_programming",
      },
      {
        id: "goal_programming",
        title: "加权与优先目标规划",
        desc: "权重平衡偏差 vs 优先因子逐级满足。",
        type: "计算方法",
        status: "ready",
        methodId: "goal_programming",
      },
    ],
  },
  {
    id: "ch7",
    title: "第七讲 · 层次分析法",
    status: "ready",
    topics: [
      {
        id: "ahp_structure",
        title: "递阶层次结构",
        desc: "目标层 / 准则层 / 方案层；为何用 AHP。",
        type: "概念",
        status: "ready",
        methodId: "ahp_structure",
        bankId: "ahp",
        casesId: "ahp",
      },
      {
        id: "ahp",
        title: "判断矩阵与一致性",
        desc: "1–9 标度、特征向量权重、CI/RI/CR；总排序。",
        type: "计算方法",
        status: "ready",
        methodId: "ahp",
      },
    ],
  },
  {
    id: "ch8",
    title: "第八讲 · 马尔可夫决策",
    status: "ready",
    topics: [
      {
        id: "markov_property",
        title: "马尔可夫性与马尔可夫链",
        desc: "无后效性；状态；齐次链（PPT 第2–7页）。",
        type: "概念",
        status: "ready",
        methodId: "markov_property",
        bankId: "markov",
        casesId: "markov",
      },
      {
        id: "markov",
        title: "转移矩阵与分布预测",
        desc: "P、S^(k)=S^(0)P^k；长期占有率。",
        type: "计算方法",
        status: "ready",
        methodId: "markov",
      },
    ],
  },
  {
    id: "ch9",
    title: "第九讲 · 多属性决策",
    status: "ready",
    topics: [
      {
        id: "madm_matrix",
        title: "问题引入与决策矩阵",
        desc: "学校扩建、研究生院评估等；先写成 Y=(y_ij)。（课堂 PPT）",
        type: "概念",
        status: "ready",
        methodId: "madm_matrix",
        bankId: "madm",
        casesId: "madm",
      },
      {
        id: "madm_preprocess",
        title: "属性预处理",
        desc: "类型多样、非量纲化、归一化（≠效用）；常用变换。（课堂 PPT）",
        type: "概念",
        status: "ready",
        methodId: "madm_preprocess",
        bankId: "madm",
        casesId: "madm",
      },
      {
        id: "madm9_prep",
        title: "预处理补充与方案初筛",
        desc: "教材§9.1：六种预处理、选优/满意值/逻辑和法（P193 起）。",
        type: "概念",
        status: "ready",
        methodId: "madm9_prep",
        bankId: "madm",
        casesId: "madm",
      },
      {
        id: "madm9_weight",
        title: "确定权重",
        desc: "教材§9.2：最小二乘、本征向量、树状/网状递推。",
        type: "概念",
        status: "ready",
        methodId: "madm9_weight",
        bankId: "madm",
        casesId: "madm",
      },
      {
        id: "madm",
        title: "综合排序方法概要",
        desc: "定权后加权和/加权积/TOPSIS 等主线方法（课堂 PPT + 教材互证）。",
        type: "计算方法",
        status: "ready",
        methodId: "madm",
      },
      {
        id: "madm9_scoring",
        title: "加权和·加权积·TOPSIS 细读",
        desc: "教材§9.3–9.5：可补偿性假设与理想解排序细节。",
        type: "计算方法",
        status: "ready",
        methodId: "madm9_scoring",
        bankId: "madm",
        casesId: "madm",
      },
      {
        id: "madm9_outranking",
        title: "ELECTRE 与 PROMETHEE",
        desc: "教材§9.7–9.8：级别高于关系与优先函数。",
        type: "计算方法",
        status: "ready",
        methodId: "madm9_outranking",
        bankId: "madm",
        casesId: "madm",
      },
    ],
  },
  {
    id: "ch10",
    title: "第十讲 · 离散事件系统与仿真",
    status: "ready",
    topics: [
      {
        id: "sim_basics",
        title: "为何仿真与系统要素",
        desc: "大纲§10.1–10.2：模型类型、八要素、仿真时钟。",
        type: "概念",
        status: "ready",
        methodId: "sim_basics",
        bankId: "discrete_sim",
        casesId: "discrete_sim",
      },
      {
        id: "discrete_sim",
        title: "九大部件与排队库存",
        desc: "大纲§10.3–10.5：事件推进；与解析期望值互补。",
        type: "概念",
        status: "ready",
        methodId: "discrete_sim",
      },
    ],
  },
];

export function findTopic(topicId) {
  for (const ch of chapters) {
    const t = ch.topics.find((x) => x.id === topicId);
    if (t) return { chapter: ch, topic: t };
  }
  return null;
}

/** 错题/旧记录可能存的是 bankId、methodId 或细知识点 id，统一解析到可进入的知识点 */
export function resolveTopicRef(refId) {
  if (!refId) return null;
  const direct = findTopic(refId);
  if (direct) return direct;

  for (const ch of chapters) {
    const byMethod = ch.topics.find((t) => t.methodId === refId);
    if (byMethod) return { chapter: ch, topic: byMethod };
  }
  for (const ch of chapters) {
    const byBank = ch.topics.find((t) => (t.bankId || t.methodId) === refId);
    if (byBank) return { chapter: ch, topic: byBank };
  }
  return null;
}

export function readyTopics() {
  return chapters.flatMap((ch) =>
    ch.topics.filter((t) => t.status === "ready").map((t) => ({ ...t, chapterTitle: ch.title }))
  );
}
