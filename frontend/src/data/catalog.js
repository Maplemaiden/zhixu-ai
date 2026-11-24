/** 课程目录：一讲一个学习台入口
 * methodId → 步骤卡/答疑主线
 * bankId / casesId → 整讲题库/案例（缺省等于 methodId）
 * 旧细知识点 id 经 TOPIC_ALIASES / resolveTopicRef 映射到本讲入口
 */

export const course = {
  name: "决策理论与方法",
  assistant: "知序 AI",
  teacher: "王军",
  blurb: "课后自主学习与答疑助教：按讲进入学习台，连续学、追问与练习。",
};

/** 原细知识点 / 旧 method·bank id → 本讲唯一 topic id */
export const TOPIC_ALIASES = {
  overview_scope: "lecture_ch1",
  overview_elements: "lecture_ch1",
  overview_types: "lecture_ch1",
  overview_process: "lecture_ch1",
  decision_overview: "lecture_ch1",

  expected_value: "lecture_ch2",
  decision_tree: "lecture_ch2",
  bayes: "lecture_ch2",

  uncertainty_setup: "lecture_ch3",
  uncertainty_criteria: "lecture_ch3",

  utility_system: "lecture_ch4",
  utility_combine: "lecture_ch4",

  dea_motivation: "lecture_ch5",
  dea: "lecture_ch5",

  gp_deviations: "lecture_ch6",
  goal_programming: "lecture_ch6",

  ahp_structure: "lecture_ch7",
  ahp: "lecture_ch7",

  markov_property: "lecture_ch8",
  markov: "lecture_ch8",

  madm_matrix: "lecture_ch9",
  madm_preprocess: "lecture_ch9",
  madm9_prep: "lecture_ch9",
  madm9_weight: "lecture_ch9",
  madm: "lecture_ch9",
  madm9_scoring: "lecture_ch9",
  madm9_outranking: "lecture_ch9",

  sim_basics: "lecture_ch10",
  discrete_sim: "lecture_ch10",
};

export const chapters = [
  {
    id: "ch1",
    title: "第一讲 · 决策理论与方法概述",
    status: "ready",
    topics: [
      {
        id: "lecture_ch1",
        title: "第一讲学习台",
        desc: "课程定位、六要素、风险/不确定分流、五原则与五步骤；本讲课件与案例。",
        type: "整讲",
        status: "ready",
        methodId: "overview_elements",
        bankId: "decision_overview",
        casesId: "decision_overview",
        outline: ["课程定位与广义决策", "决策六要素", "决策分类与分流", "五原则与五步骤"],
      },
    ],
  },
  {
    id: "ch2",
    title: "第二讲 · 风险型决策",
    status: "ready",
    topics: [
      {
        id: "lecture_ch2",
        title: "第二讲学习台",
        desc: "期望值准则（含验算）；决策树与贝叶斯在本讲连续学习，题库暂以期望值为主。",
        type: "整讲",
        status: "ready",
        methodId: "expected_value",
        bankId: "expected_value",
        casesId: "expected_value",
        outline: ["期望值准则", "决策树分析法", "贝叶斯决策分析"],
      },
    ],
  },
  {
    id: "ch3",
    title: "第三讲 · 不确定型决策分析",
    status: "ready",
    topics: [
      {
        id: "lecture_ch3",
        title: "第三讲学习台",
        desc: "不确定型适用条件与五大准则；含程序验算。",
        type: "整讲",
        status: "ready",
        methodId: "uncertainty_criteria",
        bankId: "uncertainty_criteria",
        casesId: "uncertainty_criteria",
        outline: ["不确定型适用条件", "乐观/悲观/折中/等概率/后悔值"],
      },
    ],
  },
  {
    id: "ch4",
    title: "第四讲 · 多维效用并合模型",
    status: "ready",
    topics: [
      {
        id: "lecture_ch4",
        title: "第四讲学习台",
        desc: "目标准则体系与多维效用并合规则。",
        type: "整讲",
        status: "ready",
        methodId: "utility_combine",
        bankId: "utility_combine",
        casesId: "utility_combine",
        outline: ["目标准则体系", "多维效用并合规则"],
      },
    ],
  },
  {
    id: "ch5",
    title: "第五讲 · 数据包络分析",
    status: "ready",
    topics: [
      {
        id: "lecture_ch5",
        title: "第五讲学习台",
        desc: "为何需要 DEA；DMU 与相对有效性。",
        type: "整讲",
        status: "ready",
        methodId: "dea",
        bankId: "dea",
        casesId: "dea",
        outline: ["为何需要 DEA", "DMU 与相对有效性"],
      },
    ],
  },
  {
    id: "ch6",
    title: "第六讲 · 多目标线性规划",
    status: "ready",
    topics: [
      {
        id: "lecture_ch6",
        title: "第六讲学习台",
        desc: "目标规划偏差变量；加权与优先目标规划。",
        type: "整讲",
        status: "ready",
        methodId: "goal_programming",
        bankId: "goal_programming",
        casesId: "goal_programming",
        outline: ["偏差变量", "加权与优先目标规划"],
      },
    ],
  },
  {
    id: "ch7",
    title: "第七讲 · 层次分析法",
    status: "ready",
    topics: [
      {
        id: "lecture_ch7",
        title: "第七讲学习台",
        desc: "递阶层次；判断矩阵与一致性检验。",
        type: "整讲",
        status: "ready",
        methodId: "ahp",
        bankId: "ahp",
        casesId: "ahp",
        outline: ["递阶层次结构", "判断矩阵与一致性"],
      },
    ],
  },
  {
    id: "ch8",
    title: "第八讲 · 马尔可夫决策",
    status: "ready",
    topics: [
      {
        id: "lecture_ch8",
        title: "第八讲学习台",
        desc: "马尔可夫性；转移矩阵与分布预测。",
        type: "整讲",
        status: "ready",
        methodId: "markov",
        bankId: "markov",
        casesId: "markov",
        outline: ["马尔可夫性与链", "转移矩阵与分布预测"],
      },
    ],
  },
  {
    id: "ch9",
    title: "第九讲 · 多属性决策",
    status: "ready",
    topics: [
      {
        id: "lecture_ch9",
        title: "第九讲学习台",
        desc: "决策矩阵、预处理、定权与综合排序（含 TOPSIS 等）；本讲课件与案例。",
        type: "整讲",
        status: "ready",
        methodId: "madm",
        bankId: "madm",
        casesId: "madm",
        outline: [
          "问题引入与决策矩阵",
          "属性预处理",
          "确定权重",
          "加权和·加权积·TOPSIS",
          "ELECTRE 与 PROMETHEE",
        ],
      },
    ],
  },
  {
    id: "ch10",
    title: "第十讲 · 离散事件系统与仿真",
    status: "ready",
    topics: [
      {
        id: "lecture_ch10",
        title: "第十讲学习台",
        desc: "为何仿真、系统要素；九大部件与排队库存。",
        type: "整讲",
        status: "ready",
        methodId: "discrete_sim",
        bankId: "discrete_sim",
        casesId: "discrete_sim",
        outline: ["为何仿真与系统要素", "九大部件与排队库存"],
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

/** 错题/旧记录可能存细知识点 id、bankId、methodId，统一解析到本讲学习台 */
export function resolveTopicRef(refId) {
  if (!refId) return null;

  const aliased = TOPIC_ALIASES[refId];
  if (aliased) {
    const hit = findTopic(aliased);
    if (hit) return hit;
  }

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

/** 目录用：一讲一行（每讲唯一学习台） */
export function lectureEntriesFromCatalog() {
  return chapters
    .filter((ch) => ch.status === "ready" && ch.topics.some((t) => t.status === "ready"))
    .map((ch) => {
      const topic = ch.topics.find((t) => t.status === "ready");
      return {
        chapterId: ch.id,
        chapterTitle: ch.title,
        topicId: topic.id,
        title: topic.title,
        desc: topic.desc,
        outline: topic.outline || [],
      };
    });
}
