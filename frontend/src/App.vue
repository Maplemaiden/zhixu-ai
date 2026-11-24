<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { api } from "./api";
import { useAuth } from "./composables/useAuth";
import { useSpeech } from "./composables/useSpeech";
import { addWrong, numLearned, saveProgress, store, wrongFor } from "./composables/useStore";
import AskSpace from "./components/AskSpace.vue";
import AvatarPanel from "./components/AvatarPanel.vue";
import LessonReadingPanel from "./components/LessonReadingPanel.vue";
import LoginView from "./components/LoginView.vue";
import PptClassroom from "./components/PptClassroom.vue";
import SpiritFloat from "./components/SpiritFloat.vue";
import { casesFor } from "./data/cases";
import { chapters, course, findTopic, readyTopics, resolveTopicRef } from "./data/catalog";
import { deckForChapter, hasLectureDeck } from "./data/lectureSlides";
import { narrativeFor } from "./data/topicNarratives";
import { renderRichText } from "./utils/renderRichText";

const { user, ready: authReady, isLoggedIn, bootstrap, login, register, logout } = useAuth();

const view = ref("home");
const chapterFilter = ref("all");
const search = ref("");
const activeTopicId = ref("expected_value");
const section = ref(0);
const caseIndex = ref(0);
const reviewTab = ref("summary");
const topicNotes = ref([]);
const allNotes = ref([]);
const notesLoading = ref(false);
const classroomChapterId = ref("ch2");
/** 桌面侧栏 / 目录页：讲次展开状态 */
const outlineOpen = ref(Object.fromEntries(chapters.map((ch) => [ch.id, false])));
const SIDEBAR_KEY = "zhixu_sidebar_collapsed";
const sidebarCollapsed = ref(
  (() => {
    try {
      return localStorage.getItem(SIDEBAR_KEY) === "1";
    } catch {
      return false;
    }
  })()
);

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value;
  try {
    localStorage.setItem(SIDEBAR_KEY, sidebarCollapsed.value ? "1" : "0");
  } catch {
    /* ignore */
  }
}

const health = ref(null);
const question = ref("风险型决策和不确定型决策有什么区别？");

const defaultHint = {
  goal: "按本知识点步骤卡听讲，再做案例与练习。",
  formulaLabel: "本知识点提示",
  formula: "以步骤卡展开的要点为准；不同知识点不再共用同一条口诀。",
  casePill: "案例拆解 / 验算",
  askDemo: "这一段最容易混淆的点是什么？",
  askSymbols: "本知识点里的关键术语分别指什么？",
};

const methodHints = {
  overview_scope: {
    goal: "学完后，你应能说明本课取广义决策，并区分狭义与广义。",
    formulaLabel: "课程立场",
    formula: "狭义：只选方案｜广义：发现问题 → 提出问题 → 解决问题全过程｜本课取广义（西蒙：管理就是决策）",
    casePill: "导引案例 · 田忌赛马看整体策略",
    askDemo: "为什么本课强调广义决策，而不是只学怎么选方案？",
    askSymbols: "狭义决策和广义决策分别指什么？",
  },
  overview_elements: {
    goal: "学完后，你应能用鸡蛋煎饼例说出六要素，并分清状态与方案。",
    formulaLabel: "六要素口诀（仅本知识点）",
    formula: "决策者 → 目标 → 方案 → 自然状态 → 结果 → 准则\n状态不可控但可预见；方案可控。分不清后面损益表会建反。",
    casePill: "鸡蛋煎饼 · 逐项对齐六要素",
    askDemo: "鸡蛋煎饼例里，自然状态和行动方案分别是什么？",
    askSymbols: "决策六要素各是什么？状态和方案怎么区分？",
  },
  overview_types: {
    goal: "学完后，你应能按有无概率分流风险型与不确定型。",
    formulaLabel: "最重要分流",
    formula: "有概率 → 风险型（第二讲期望值等）\n无概率 → 不确定型（第三讲五准则）\n先判类型，再选方法。",
    casePill: "风险型 vs 不确定型对照",
    askDemo: "风险型和不确定型唯一差别是什么？",
    askSymbols: "确定型、风险型、不确定型分别怎么划分？",
  },
  overview_process: {
    goal: "学完后，你应能复述五原则与五步骤，并说明目标三性。",
    formulaLabel: "五步骤口诀",
    formula: "形成问题 → 定目标 → 拟方案 → 选方案 → 实施反馈\n目标要有针对性、准确性、约束性。",
    casePill: "五步骤检查清单",
    askDemo: "科学决策的五步骤按什么顺序？",
    askSymbols: "五原则和目标三性分别是什么？",
  },
  decision_overview: {
    goal: "学完后，你应能说明这门课学什么、为何取广义决策，并掌握六要素、风险/不确定分流与五步骤。",
    formulaLabel: "第一讲总览",
    formula: "先定广义决策 → 再学六要素 → 再按有无概率分流 → 最后用五步骤落地",
    casePill: "教材案例拆解 · 先对齐概念，再进入后面计算讲",
    askDemo: "这门课主要解决什么问题？为什么先学概述而不是直接算期望值？",
    askSymbols: "第一讲里广义决策、六要素和风险/不确定分流分别解决什么？",
  },
  utility_combine: {
    goal: "学完后，你应能说明目标准则体系三原则，并区分序列型结构与常用效用并合规则。",
    formulaLabel: "距离并合（示意，见第四讲教案）",
    formula: "W(u₁,u₂)=1−√½[(1−u₁)²+(1−u₂)²]",
    casePill: "教案规则对照 · 注明教材第5章位置",
    askDemo: "多维效用并合适用于哪种目标准则体系结构？",
    askSymbols: "效用并合里 u、W、H 和并合运算∘分别表示什么？",
  },
  dea: {
    goal: "学完后，你应能说明何时传统比率失效，以及 DMU、投入产出与相对有效性含义。",
    formulaLabel: "相对效率思想（示意）",
    formula: "max (uᵀy₀)/(vᵀx₀)（CCR 比率形式，细节见第五讲）",
    casePill: "教案四引例拆解 · 量纲不同为何需要 DEA",
    askDemo: "第五讲引例4为什么说明必须引入 DEA？",
    askSymbols: "DEA 里 DMU、投入、产出分别指什么？相对有效是什么意思？",
  },
  goal_programming: {
    goal: "学完后，你应能写出正负偏差变量含义，并区分加权目标规划与优先目标规划。",
    formulaLabel: "达成函数（加权示意）",
    formula: "min Σ (w⁻d⁻ + w⁺d⁺)",
    casePill: "偏差变量与优先级 · 对齐第六讲符号",
    askDemo: "目标规划为什么不要求所有目标都精确最优？",
    askSymbols: "d_k^- 与 d_k^+ 分别表示什么？优先因子法有何约束？",
  },
  ahp: {
    goal: "学完后，你应能说出 AHP 四步，并解释判断矩阵与 CR 一致性检验。",
    formulaLabel: "一致性（教案）",
    formula: "CI=(λ_max−n)/(n−1)，CR=CI/RI",
    casePill: "层次结构与判断矩阵 · 对齐第七讲教案",
    askDemo: "AHP 为什么适合难以直接量化的多准则问题？",
    askSymbols: "判断矩阵、λ_max、CI、RI、CR 各是什么？",
  },
  markov: {
    goal: "学完后，你应能说明马尔可夫性，并用转移矩阵做状态分布预测。",
    formulaLabel: "分布预测",
    formula: "S^(k)=S^(0)P^k",
    casePill: "转移矩阵读写 · 对齐第八讲 PPT 页码",
    askDemo: "什么是无后效性（马尔可夫性）？",
    askSymbols: "一步转移概率 p_ij 与转移矩阵 P 怎么读？",
  },
  discrete_sim: {
    goal: "学完后，你应能说明为何仿真，并列举离散事件系统要素与九大部件。",
    formulaLabel: "概念框架",
    formula: "事件推进：初始化 → 定时取下一事件 → 更新状态/统计",
    casePill: "大纲第十讲要点拆解 · 含教材页码提示",
    askDemo: "仿真时钟和计算机运行时间有什么区别？",
    askSymbols: "实体、事件、仿真时钟、事件表分别指什么？",
  },
  madm: {
    goal: "学完后，你应能用决策矩阵描述问题，并说明属性预处理的原因与常用变换。",
    formulaLabel: "标准0-1（效益型示意）",
    formula: "z_ij=(y_ij−ymin)/(ymax−ymin)",
    casePill: "决策矩阵与预处理 · 对齐第九讲 PPT / 教材第九章",
    askDemo: "多属性决策为什么要做数据预处理？",
    askSymbols: "效益型与成本型属性在规范化时有何不同？",
  },
  expected_value: {
    goal: "学完后，你应能说明期望值准则的前提，并按期望损益值选优。",
    formulaLabel: "期望值（示意）",
    formula: "E(aᵢ) = Σ payoffsᵢⱼ × pⱼ",
    casePill: "模拟数据 · 后端真实执行期望值演算",
    askDemo: "期望值准则的前提是什么？",
    askSymbols: "期望值准则里 E、θ、p、a 分别表示什么？标准公式怎么写？",
  },
  decision_tree: {
    goal: "学完后，你应能识别决策点与状态点，并说明从右向左回推剪枝的思路。",
    formulaLabel: "决策树回推（示意）",
    formula: "E(状态点) = Σ 结果值 × 概率；决策点取最优枝",
    casePill: "单阶段树 · 用等价收益表做期望值回推验算",
    askDemo: "决策树里方框和圆圈分别表示什么？",
    askSymbols: "决策树中决策点、状态点与节点期望值 E 怎么对应？回推公式怎么写？",
  },
  bayes: {
    goal: "学完后，你应能说出先验→后验的修正思路，并用后验概率做期望值决策。",
    formulaLabel: "贝叶斯修正（示意）",
    formula: "P(θ|I) ∝ P(I|θ) · P(θ)  →  再用后验算 E(a)",
    casePill: "后验已给定 · 后端按期望值准则验算选优",
    askDemo: "贝叶斯决策和普通期望值决策差在哪里？",
    askSymbols: "先验 P(θ)、后验 P(θ|I) 与补充信息 I 分别是什么？贝叶斯公式怎么写？",
  },
  uncertainty_criteria: {
    goal: "学完后，你应能区分五准则，并说明同一收益表下为何可能选不同方案。",
    formulaLabel: "五大准则怎么选（收益型）",
    formula:
      "乐观：看每个方案的最好结果，再选其中最好的那个方案\n悲观：看每个方案的最差结果，再选其中最好的那个方案\n折中：把最好与最差按系数α加权后比较\n等概率：假定各状态一样可能，取平均后比较\n后悔值：先算相对最优的后悔，再选「最大后悔」最小的方案",
    casePill: "无概率 · 后端按所选准则程序验算",
    askDemo: "不确定型决策的乐观准则和悲观准则有何不同？",
    askSymbols: "不确定型五准则里 α、后悔值 R 是什么？各准则指标怎么表示？",
  },
};

const askLoading = ref(false);
const askResult = ref(null);
const askError = ref("");
const chat = ref([]);

const computeResult = ref(null);
const computeLoading = ref(false);
const computeError = ref("");
const caseBrief = ref(null);

const quizItems = ref([]);
const quizIndex = ref(0);
const quizChoice = ref(null);
const quizChecked = ref(false);
const quizFeedback = ref(null);
const lessonReading = ref([]);
const lessonReadingSource = ref("");
const stepCard = ref(null);
const askOpen = ref(false);
const pendingSection = ref(null);
/** 首页大知知是否仍在视口内；在则隐藏浮层小知知，避免双份 */
const heroArtEl = ref(null);
const heroZhizhiInView = ref(true);
let heroObserver = null;
/** 课件页口播状态（供浮层知知同步） */
const pptRef = ref(null);
const classroomSpeaking = ref(false);
const classroomLine = ref("");

const lessonParts = ["讲解", "做题答疑"];
function persistLesson(topicId, sec = section.value) {
  saveProgress(topicId, {
    section: sec,
    lessonMode: sec === 1 ? "practice" : "teach",
    caseIndex: caseIndex.value,
  });
}
const { speaking, paused, currentLine, supported, stop, pause, resume, speakLines, speakText } = useSpeech();

const backendOk = computed(() => health.value?.ok === true);
const current = computed(() => resolveTopicRef(activeTopicId.value));
const topicReady = computed(() => current.value?.topic?.status === "ready");

/** 把旧 id / methodId / bankId 收成可进入的 ready 知识点 */
function resolveReadyTopicId(refId) {
  const hit = resolveTopicRef(refId);
  if (hit?.topic?.status === "ready") return hit.topic.id;

  const progressIds = Object.keys(store.progress || {}).sort(
    (a, b) => (store.progress[b]?.updated || 0) - (store.progress[a]?.updated || 0)
  );
  for (const pid of progressIds) {
    const p = resolveTopicRef(pid);
    if (p?.topic?.status === "ready") return p.topic.id;
  }
  return readyTopics()[0]?.id || "expected_value";
}
const methodId = computed(
  () => current.value?.topic?.methodId || activeTopicId.value || "expected_value"
);
const bankId = computed(() => current.value?.topic?.bankId || methodId.value);
const casesId = computed(() => current.value?.topic?.casesId || methodId.value);
const hint = computed(() => methodHints[methodId.value] || defaultHint);
const topicCases = computed(() => casesFor(casesId.value));
const activeCase = computed(() => {
  const list = topicCases.value;
  if (!list.length) return null;
  return list[caseIndex.value % list.length];
});
const isWalkthroughCase = computed(() => !!activeCase.value && !activeCase.value.computeKind);
/** 导入/步骤叙事：只用本知识点步骤卡；不再回退整讲叙事（避免六要素口诀串台） */
const overviewStory = computed(() => {
  const fromApi = stepCard.value?.intro_story;
  if (fromApi?.length) return fromApi;
  return narrativeFor(methodId.value)?.intro_story || [];
});
const overviewDetails = computed(() => {
  const fromApi = stepCard.value?.step_details;
  if (fromApi?.length) return fromApi;
  return narrativeFor(methodId.value)?.step_details || [];
});
const hasRichIntro = computed(() => overviewStory.value.length > 0);
const topicWrong = computed(() => wrongFor(activeTopicId.value));
const flatTopics = computed(() =>
  chapters.flatMap((ch) => ch.topics.map((t) => ({ ...t, chapterTitle: ch.title, chapterId: ch.id })))
);
const filteredTopics = computed(() => {
  const q = search.value.trim().toLowerCase();
  return flatTopics.value.filter((t) => {
    const chapOk = chapterFilter.value === "all" || t.chapterId === chapterFilter.value;
    const text = `${t.title}${t.desc}${t.chapterTitle}`.toLowerCase();
    return chapOk && (!q || text.includes(q));
  });
});
const crumb = computed(() => {
  if (view.value === "home") return "首页";
  if (view.value === "catalog") return "课程学习 / 知识点目录";
  if (view.value === "qa") return "答疑空间";
  if (view.value === "classroom") {
    const d = activeDeck.value;
    return d ? `课程学习 / ${d.chapterTitle} / 课件讲解` : "课件讲解";
  }
  if (view.value === "review") {
    if (reviewTab.value === "notes") return "复习与记录 / 我的标注";
    if (reviewTab.value === "wrong") return "复习与记录 / 历史错题";
    return "复习与记录";
  }
  if (view.value === "lesson" && current.value) {
    return `课程学习 / ${current.value.chapter.title} / ${current.value.topic.title} / ${lessonParts[section.value]}`;
  }
  return "";
});
const noteCount = computed(() => allNotes.value.length);
const activeDeck = computed(() => deckForChapter(classroomChapterId.value));
const lectureEntries = computed(() =>
  chapters
    .filter((ch) => hasLectureDeck(ch.id))
    .map((ch) => ({
      id: ch.id,
      title: ch.title,
      deckTitle: deckForChapter(ch.id)?.title || ch.title,
      slideCount: deckForChapter(ch.id)?.slides?.length || 0,
    }))
);

const homeContinue = computed(() => {
  const id = resolveReadyTopicId(store.lastTopicId || "expected_value");
  const hit = resolveTopicRef(id);
  const title = hit?.topic?.title || "期望值准则";
  const chapterTitle = hit?.chapter?.title || "";
  return {
    topicId: id,
    chapterId: hit?.chapter?.id || "ch2",
    title,
    chapterTitle,
    eyebrow: "今天，从这里开始",
    headline: `你好，今天我们学${title}。`,
    continueFrom: chapterTitle ? `${chapterTitle} · ${title}` : title,
  };
});

function toggleOutline(chapterId) {
  outlineOpen.value = {
    ...outlineOpen.value,
    [chapterId]: !outlineOpen.value[chapterId],
  };
}

function selectChapterFilter(chapterId) {
  chapterFilter.value = chapterId;
  if (chapterId !== "all") {
    outlineOpen.value = { ...outlineOpen.value, [chapterId]: true };
  }
  if (view.value !== "catalog") go("catalog");
}

function openClassroom(chapterId) {
  if (!hasLectureDeck(chapterId)) return;
  stop();
  classroomChapterId.value = chapterId;
  askOpen.value = false;
  view.value = "classroom";
}

watch(
  view,
  (v) => {
    const lock = v === "classroom" || v === "qa";
    document.documentElement.style.overflow = lock ? "hidden" : "";
    document.body.style.overflow = lock ? "hidden" : "";
    if (v !== "classroom") {
      classroomSpeaking.value = false;
      classroomLine.value = "";
    }
  },
  { immediate: true }
);

watch(
  () => current.value?.chapter?.id,
  (id) => {
    if (id) outlineOpen.value = { ...outlineOpen.value, [id]: true };
  }
);
const nextReady = computed(() => {
  const list = readyTopics();
  const i = list.findIndex((t) => t.id === activeTopicId.value);
  if (!list.length) return null;
  if (i < 0) return list[0];
  return list[(i + 1) % list.length];
});
const sessionLabel = computed(() => {
  const t = current.value?.topic?.title;
  if (!t) return "尚未进入知识点";
  return `${t} · ${lessonParts[section.value]}`;
});
const coach = computed(() => {
  const title = current.value?.topic?.title || "本知识点";
  if (section.value === 0) {
    return {
      now: `正在学：${title} · 讲解`,
      tip: stepCard.value?.source ? `来源：${stepCard.value.source}` : "先把本知识点听完，再去做小测答疑。",
      primary: { label: "结束讲解，去做小测答疑", run: "practice" },
      secondary: [{ label: "听本讲口播", run: "play" }],
    };
  }
  if (quizChecked.value && quizFeedback.value?.correct) {
    return {
      now: `正在学：${title} · 小测通过`,
      tip: nextReady.value ? `可以继续「${nextReady.value.title}」，或再练一题。` : "可以再练一题巩固。",
      primary: nextReady.value
        ? { label: `下一知识点：${nextReady.value.title}`, run: "next-topic" }
        : { label: "再练一题", run: "retry-quiz" },
      secondary: [
        { label: "再练一题", run: "retry-quiz" },
        { label: "返回讲解", run: "teach" },
      ],
    };
  }
  if (quizChecked.value && quizFeedback.value && !quizFeedback.value.correct) {
    return {
      now: `正在学：${title} · 本题需巩固`,
      tip: "错题已收入复习本。可返回讲解对照步骤，或直接追问错因。",
      primary: { label: "返回讲解重听", run: "reteach" },
      secondary: [
        { label: "追问错因", run: "ask" },
        { label: "去复习本", run: "review" },
      ],
    };
  }
  return {
    now: `正在学：${title} · 做题答疑`,
    tip: "做题检验掌握；不会的就在本页追问，不必跳来跳去。",
    primary: { label: "返回讲解", run: "teach" },
    secondary: [{ label: "追问本题", run: "ask" }],
  };
});
const caseAskPreset = computed(() => {
  const c = activeCase.value;
  if (!c) return "";
  const title = caseBrief.value?.title || c.title;
  if (isWalkthroughCase.value) {
    return `请结合当前案例「${title}」说明：它分别对应决策六要素里的哪些项？自然状态和行动方案在本例中是什么？`;
  }
  if (computeResult.value?.best) {
    return `刚才程序验算最优方案是「${computeResult.value.best}」，请按教材符号说明为什么是它。结合案例：${title}`;
  }
  return `请结合当前案例「${title}」说明适用条件与关键步骤。`;
});

const askSuggestions = computed(() => {
  const base = [hint.value.askDemo, hint.value.askSymbols, "风险型决策和不确定型决策有什么区别？"];
  if (section.value === 2 && caseAskPreset.value) {
    return [caseAskPreset.value, ...base.filter((q) => q !== caseAskPreset.value)];
  }
  return base;
});
async function refreshTopicNotes() {
  if (!isLoggedIn.value || !topicReady.value) {
    topicNotes.value = [];
    return;
  }
  try {
    const data = await api.listNotes(methodId.value);
    topicNotes.value = data.items || [];
  } catch {
    topicNotes.value = [];
  }
}

async function refreshAllNotes() {
  if (!isLoggedIn.value) {
    allNotes.value = [];
    return;
  }
  notesLoading.value = true;
  try {
    const data = await api.listNotes();
    allNotes.value = data.items || [];
  } catch {
    allNotes.value = [];
  } finally {
    notesLoading.value = false;
  }
}

async function createLessonNote(payload) {
  const data = await api.createNote({
    method_id: methodId.value,
    quote: payload.quote,
    section_index: payload.section_index ?? 0,
    color: payload.color || "amber",
    tag: payload.tag || "",
    remark: payload.remark || "",
  });
  topicNotes.value = [data.item, ...topicNotes.value];
  allNotes.value = [data.item, ...allNotes.value.filter((n) => n.id !== data.item.id)];
  return data.item;
}

async function removeNote(id) {
  await api.deleteNote(id);
  topicNotes.value = topicNotes.value.filter((n) => n.id !== id);
  allNotes.value = allNotes.value.filter((n) => n.id !== id);
}

function noteTopicTitle(methodOrTopicId) {
  const byId = findTopic(methodOrTopicId);
  if (byId) return byId.topic.title;
  const hit = readyTopics().find((t) => t.methodId === methodOrTopicId || t.id === methodOrTopicId);
  return hit?.title || methodOrTopicId;
}

function openNoteTarget(note) {
  const byId = findTopic(note.method_id);
  if (byId) {
    openTopic(byId.topic.id, { section: 0 });
    return;
  }
  const hit = readyTopics().find((t) => t.methodId === note.method_id || t.id === note.method_id);
  if (hit) openTopic(hit.id, { section: 0 });
}

async function handleLogout() {
  stop();
  await logout();
  topicNotes.value = [];
  allNotes.value = [];
  view.value = "home";
}

function teardownHeroObserver() {
  if (heroObserver) {
    heroObserver.disconnect();
    heroObserver = null;
  }
}

function setupHeroObserver() {
  teardownHeroObserver();
  if (view.value !== "home" || !heroArtEl.value) {
    heroZhizhiInView.value = false;
    return;
  }
  heroZhizhiInView.value = true;
  heroObserver = new IntersectionObserver(
    ([entry]) => {
      heroZhizhiInView.value = !!entry?.isIntersecting;
    },
    { root: null, threshold: 0 }
  );
  heroObserver.observe(heroArtEl.value);
}

const spiritFloatVisible = computed(
  () =>
    view.value !== "qa" &&
    !(view.value === "home" && heroZhizhiInView.value)
);

function onClassroomSpeech({ speaking: sp, line } = {}) {
  classroomSpeaking.value = !!sp;
  classroomLine.value = line || "";
}

function stopSpiritExternal() {
  if (view.value === "classroom") {
    pptRef.value?.stopAll?.();
    classroomSpeaking.value = false;
    classroomLine.value = "";
    return;
  }
  stop();
}

onMounted(async () => {
  await bootstrap();
  try {
    health.value = await api.health();
  } catch (e) {
    health.value = null;
  }
  if (isLoggedIn.value) {
    store.lastTopicId = resolveReadyTopicId(store.lastTopicId);
    activeTopicId.value = resolveReadyTopicId(activeTopicId.value || store.lastTopicId);
    await loadTopicAssets();
    restoreTopicProgress();
    await refreshAllNotes();
    await nextTick();
    setupHeroObserver();
  }
});
onUnmounted(() => {
  teardownHeroObserver();
  stop();
});

watch(activeTopicId, async () => {
  section.value = 0;
  caseIndex.value = 0;
  quizIndex.value = 0;
  quizChoice.value = null;
  quizChecked.value = false;
  quizFeedback.value = null;
  computeResult.value = null;
  caseBrief.value = null;
  computeError.value = "";
  stop();
  await loadTopicAssets();
  restoreTopicProgress();
  if (pendingSection.value != null) {
    section.value = pendingSection.value >= 1 ? 1 : 0;
    pendingSection.value = null;
    persistLesson(activeTopicId.value);
  } else {
    // 普通进入知识点：总是从讲解开头看，不跳到上次停在的做题答疑底部
    section.value = 0;
    askOpen.value = false;
  }
  if (section.value === 1) askOpen.value = true;
  scrollLessonTop();
});

watch([section, caseIndex], () => {
  if (topicReady.value) persistLesson(activeTopicId.value);
});

watch(view, async (v) => {
  if (v === "lesson") scrollLessonTop();
  await nextTick();
  setupHeroObserver();
});

watch(isLoggedIn, async (ok) => {
  if (!ok) {
    teardownHeroObserver();
    return;
  }
  try {
    health.value = await api.health();
  } catch {
    health.value = null;
  }
  store.lastTopicId = resolveReadyTopicId(store.lastTopicId);
  activeTopicId.value = resolveReadyTopicId(activeTopicId.value || store.lastTopicId);
  await loadTopicAssets();
  restoreTopicProgress();
  await refreshAllNotes();
  await nextTick();
  setupHeroObserver();
});

function scrollLessonTop() {
  nextTick(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    const main = document.querySelector(".main");
    if (main) main.scrollTop = 0;
  });
}

function restoreTopicProgress() {
  const p = store.progress[activeTopicId.value];
  if (p) {
    // 只恢复案例情境；讲解/做题由本次进入意图决定
    caseIndex.value = p.caseIndex ?? 0;
  }
}

async function loadTopicAssets() {
  if (!topicReady.value) {
    stepCard.value = null;
    quizItems.value = [];
    lessonReading.value = [];
    lessonReadingSource.value = "";
    return;
  }
  const mid = methodId.value;
  try {
    const sc = await api.stepCard(mid);
    stepCard.value = sc.card;
  } catch {
    stepCard.value = null;
  }
  try {
    const bank = await api.listQuiz(bankId.value);
    quizItems.value = bank.items || [];
  } catch {
    quizItems.value = [];
  }
  try {
    const reading = await api.lessonReading(mid);
    lessonReading.value = reading.sections || [];
    lessonReadingSource.value = reading.source || "";
  } catch {
    lessonReading.value = [];
    lessonReadingSource.value = "";
  }
  await refreshTopicNotes();
}

function go(v) {
  view.value = v;
  if (v !== "lesson") askOpen.value = false;
  if (v === "review") refreshAllNotes();
  stop();
}

function openQaSpace() {
  askOpen.value = false;
  stop();
  view.value = "qa";
}
function openTopic(id, opts = {}) {
  const hit = resolveTopicRef(id);
  const topicId = hit?.topic?.id || resolveReadyTopicId(id);
  const same = activeTopicId.value === topicId;
  store.lastTopicId = topicId;
  if (opts.ask) pendingSection.value = 1;
  else if (opts.section != null) pendingSection.value = opts.section >= 1 ? 1 : 0;
  else pendingSection.value = 0;
  askOpen.value = !!opts.ask;
  if (opts.question) question.value = opts.question;
  activeTopicId.value = topicId;
  view.value = "lesson";
  if (same) {
    section.value = pendingSection.value >= 1 ? 1 : 0;
    pendingSection.value = null;
    if (section.value === 1) askOpen.value = true;
    persistLesson(topicId);
    scrollLessonTop();
  } else {
    persistLesson(topicId, askOpen.value || opts.section >= 1 ? 1 : 0);
  }
}
function openAsk(preset) {
  if (preset) question.value = preset;
  const id = resolveReadyTopicId(store.lastTopicId || activeTopicId.value || "expected_value");
  if (view.value !== "lesson") openTopic(id, { section: 1, ask: true });
  else {
    if (section.value !== 1) gotoSection(1, { speak: false });
    askOpen.value = true;
  }
}
function gotoSection(i, { speak = true } = {}) {
  section.value = Math.max(0, Math.min(1, i));
  if (section.value === 1) askOpen.value = true;
  else askOpen.value = false;
  scrollLessonTop();
  if (speak) playSection();
}

function sectionSpeech() {
  const t = current.value?.topic;
  if (!t) return [];
  if (section.value === 0) {
    const lines = [stepCard.value?.speak_intro || `欢迎学习${t.title}。`];
    const story = overviewStory.value;
    if (story?.length) lines.push(...story);
    else lines.push(t.desc);
    if (lessonReading.value?.length) {
      lines.push("下面按课程讲义讲解。");
      lessonReading.value.slice(0, 2).forEach((sec) => {
        lines.push(sec.title);
        lines.push(String(sec.text || "").replace(/[#|*`]/g, " ").replace(/\s+/g, " ").slice(0, 220));
      });
    }
    const details = overviewDetails.value;
    if (details?.length) {
      lines.push("本讲提纲如下。");
      details.forEach((d, i) => {
        lines.push(`第${i + 1}部分：${d.title}。`);
        (d.points || []).forEach((p) => lines.push(p));
      });
    } else {
      const steps = stepCard.value?.steps || [];
      lines.push(...steps.map((s, i) => `第${i + 1}步：${s}`));
    }
    const c = activeCase.value;
    if (c) lines.push(c.title, c.intro);
    lines.push("讲解结束后，可以去做小测答疑。");
    return lines;
  }
  return [
    `现在进入做题答疑：做一道练习，检验你是否掌握${t.title}。`,
    "不会的题目可以直接追问；答错会进入错题记录。",
  ];
}

function playSection() {
  speakLines(sectionSpeech());
}
function onPause() {
  pause();
}
function onResume() {
  resume();
}
function prevSection() {
  if (section.value > 0) gotoSection(section.value - 1);
}
function nextSection() {
  if (section.value < 1) gotoSection(section.value + 1);
}
function changeCase() {
  caseIndex.value = (caseIndex.value + 1) % Math.max(topicCases.value.length, 1);
  computeResult.value = null;
  caseBrief.value = null;
  computeError.value = "";
}

function runCaseWalkthrough() {
  const c = activeCase.value;
  if (!c || c.computeKind) return;
  caseBrief.value = {
    title: c.title,
    panel: c.panel || "",
    takeaway: c.takeaway || "",
  };
  speakLines([
    ...(c.speak || [c.title, c.intro]),
    c.takeaway || "案例讲完了。可以继续听本讲，或结束讲解去做小测。",
  ]);
}

async function runCaseCompute() {
  const c = activeCase.value;
  if (!c?.computeKind) {
    runCaseWalkthrough();
    return;
  }
  computeLoading.value = true;
  computeError.value = "";
  try {
    if (c.computeKind === "uncertainty") {
      computeResult.value = await api.computeUncertainty(c.payload);
    } else {
      computeResult.value = await api.computeEV(c.payload);
    }
    speakLines([
      ...(computeResult.value.speak_lines || []),
      "验算完成。可以继续看讲解，或结束讲解去做小测答疑。",
    ]);
  } catch (e) {
    computeError.value = e.message || String(e);
  } finally {
    computeLoading.value = false;
  }
}

async function doAsk() {
  askLoading.value = true;
  askError.value = "";
  try {
    const q = question.value.trim();
    chat.value.push({ role: "user", text: q });
    const res = await api.ask(q, methodId.value, {
      section: section.value,
      sectionLabel: lessonParts[section.value],
    });
    askResult.value = res;
    chat.value.push({
      role: "assistant",
      text: res.answer,
      sources: res.sources,
      topic: current.value?.topic?.title,
    });
    askOpen.value = true;
  } catch (e) {
    askError.value = e.message || String(e);
  } finally {
    askLoading.value = false;
  }
}

function speakAsk() {
  if (askResult.value?.answer) speakText(String(askResult.value.answer).replace(/\s+/g, " ").slice(0, 280));
}

const choiceQuizzes = computed(() => quizItems.value.filter((x) => x.type === "choice"));
const currentQuiz = computed(() => {
  const list = choiceQuizzes.value;
  if (!list.length) return quizItems.value[0] || null;
  return list[quizIndex.value % list.length];
});

async function submitQuiz() {
  const item = currentQuiz.value;
  if (!item || item.type !== "choice") return;
  if (quizChoice.value == null) return;
  const fb = await api.grade({ question_id: item.id, choice: quizChoice.value });
  quizFeedback.value = fb;
  quizChecked.value = true;
  if (!fb.correct) {
    addWrong({
      topic: activeTopicId.value,
      question: item.question,
      chosen: `${quizChoice.value}. ${item.options[quizChoice.value]}`,
      correct: `${item.answer}. ${item.options[item.answer]}`,
      reason: fb.reason || item.reason,
    });
  }
  if (fb.correct) {
    speakLines([
      ...(fb.speak || []),
      nextReady.value ? `这题过了。可以继续学习${nextReady.value.title}，或再练一题。` : "这题过了。可以再练一题巩固。",
    ]);
  } else {
    speakLines([
      ...(fb.speak || []),
      "建议不要离开这个知识点。按教材步骤卡把这道题再听一遍。",
    ]);
  }
}

function resetQuiz() {
  quizChoice.value = null;
  quizChecked.value = false;
  quizFeedback.value = null;
}

function nextQuiz() {
  const n = choiceQuizzes.value.length;
  if (!n) return;
  quizIndex.value = (quizIndex.value + 1) % n;
  resetQuiz();
}

function reteachWrong() {
  askOpen.value = false;
  gotoSection(0, { speak: false });
  speakLines([
    "我们回到讲解，按教材步骤把这道题再过一遍。",
    ...(stepCard.value?.steps || []),
    quizFeedback.value?.reason || "对照步骤，看哪一步判断反了。",
  ]);
}

/** 复习本：回到对应知识点的「讲解」段，并带上错因提示 */
function openWrongReteach(w) {
  const hit = resolveTopicRef(w?.topic);
  if (!hit) {
    go("catalog");
    return;
  }
  const reason = w?.reason || "";
  const q = w?.question || "";
  openTopic(hit.topic.id, {
    section: 0,
    ask: false,
    question: q ? `请按教材步骤重讲这道错题：${q}${reason ? `。错因提示：${reason}` : ""}` : undefined,
  });
  // openTopic 异步切课后再口播；短延迟等步骤卡加载
  setTimeout(() => {
    speakLines([
      "我们回到这道错题对应的知识点，先按讲解把概念理清。",
      reason || "对照正确选项，看哪一步判断反了。",
      "听完讲解后，可以再去做题答疑巩固。",
    ]);
  }, 600);
}

function sectionAskPreset() {
  if (section.value === 1 && currentQuiz.value) {
    return `请按教材步骤讲这道题：${currentQuiz.value.question}`;
  }
  if (activeCase.value && (caseBrief.value || computeResult.value)) return caseAskPreset.value;
  return hint.value.askDemo;
}

function runCoach(run) {
  if (run === "practice" || run === "quiz") gotoSection(1);
  else if (run === "teach") gotoSection(0);
  else if (run === "play") playSection();
  else if (run === "ask") openAsk(sectionAskPreset());
  else if (run === "ask-compute") openAsk(sectionAskPreset());
  else if (run === "compute") runCaseCompute();
  else if (run === "walkthrough") runCaseWalkthrough();
  else if (run === "change-case") changeCase();
  else if (run === "next-topic" && nextReady.value) openTopic(nextReady.value.id, { section: 0 });
  else if (run === "retry-quiz") {
    if (choiceQuizzes.value.length > 1) nextQuiz();
    else resetQuiz();
  }
  else if (run === "reteach") reteachWrong();
  else if (run === "review") {
    reviewTab.value = "wrong";
    go("review");
  }
}

</script>

<template>
  <div v-if="!authReady" class="boot-screen">正在恢复登录状态…</div>
  <LoginView v-else-if="!isLoggedIn" :do-login="login" :do-register="register" />
  <template v-else>
  <PptClassroom
    v-if="view === 'classroom' && activeDeck"
    ref="pptRef"
    :deck="activeDeck"
    @back="go('catalog')"
    @open-topic="(id) => openTopic(id)"
    @speech="onClassroomSpeech"
  />
  <AskSpace
    v-else-if="view === 'qa'"
    :backend-ok="backendOk"
    @back="go('home')"
  />
  <div v-else class="shell">
    <aside class="sidebar desktop-only" :class="{ collapsed: sidebarCollapsed }">
      <div class="brand">
        <div class="brand-mark">知</div>
        <div class="brand-copy">
          <div class="brand-text">{{ course.assistant }}</div>
          <div class="brand-sub">决策理论与方法</div>
        </div>
        <button
          class="sidebar-toggle"
          type="button"
          :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'"
          :aria-label="sidebarCollapsed ? '展开侧栏' : '收起侧栏'"
          :aria-expanded="!sidebarCollapsed"
          @click="toggleSidebar"
        >
          {{ sidebarCollapsed ? "›" : "‹" }}
        </button>
      </div>
      <button
        class="nav-item"
        :class="{ active: view === 'home' }"
        type="button"
        title="首页"
        @click="go('home')"
      >
        <span class="nav-short">首</span>
        <span class="nav-label">首页</span>
      </button>
      <button
        class="nav-item"
        :class="{ active: view === 'catalog' || (view === 'lesson' && !askOpen) }"
        type="button"
        title="课程学习"
        @click="go('catalog')"
      >
        <span class="nav-short">课</span>
        <span class="nav-label">课程学习</span>
      </button>
      <button
        class="nav-item"
        :class="{ active: view === 'qa' }"
        type="button"
        title="答疑空间"
        @click="openQaSpace()"
      >
        <span class="nav-short">问</span>
        <span class="nav-label">答疑空间</span>
      </button>
      <button
        v-if="view === 'lesson'"
        class="nav-item"
        :class="{ active: askOpen }"
        type="button"
        title="课中追问"
        @click="openAsk()"
      >
        <span class="nav-short">追</span>
        <span class="nav-label">课中追问</span>
      </button>
      <button
        class="nav-item"
        :class="{ active: view === 'review' }"
        type="button"
        title="复习与记录"
        @click="go('review')"
      >
        <span class="nav-short">记</span>
        <span class="nav-label">复习与记录</span>
      </button>

      <div class="sidebar-bottom">
        <div class="user-mini">
          <div class="user-icon" :title="user?.display_name || user?.username || '学生'">
            {{ (user?.display_name || user?.username || "学").slice(0, 1) }}
          </div>
          <div class="user-meta">
            {{ user?.display_name || user?.username || "学生" }}
            <small>@{{ user?.username }} · <button type="button" class="logout-link" @click="handleLogout">退出</button></small>
          </div>
        </div>
      </div>
    </aside>

    <header class="m-app-header mobile-only">
      <div class="m-brand">
        <div class="brand-mark">知</div>
        <div class="m-brand-text">
          <strong>知序 AI</strong>
          <small>{{ view === "lesson" ? current?.topic?.title || "学习中" : crumb }}</small>
        </div>
      </div>
      <button class="m-user-chip" type="button" @click="handleLogout" title="退出登录">
        {{ (user?.display_name || user?.username || "学").slice(0, 1) }}
      </button>
    </header>

    <main class="main">
      <div class="topbar desktop-only">
        <div class="breadcrumb">{{ crumb }}</div>
      </div>
      <div class="m-status-bar mobile-only">
        <span>{{ user?.display_name || user?.username }}</span>
      </div>

      <div class="content" :class="{ 'home-mode': view === 'home' }">
        <!-- HOME -->
        <template v-if="view === 'home'">
          <div class="home-screen">
            <section class="hero">
              <div class="hero-glow" aria-hidden="true" />
              <div class="hero-copy">
                <div class="hero-brand">
                  <span class="hero-mark">知</span>
                  <strong>知序 AI</strong>
                </div>
                <p class="hero-eyebrow">{{ homeContinue.eyebrow }}</p>
                <h1>{{ homeContinue.headline }}</h1>
                <div class="hero-buttons">
                  <button class="btn" type="button" @click="go('catalog')">开始学习</button>
                  <div class="hero-continue">
                    <button class="btn btn-primary" type="button" @click="openTopic(homeContinue.topicId)">
                      继续学习 →
                    </button>
                    <span class="hero-continue-from">从「{{ homeContinue.continueFrom }}」继续</span>
                  </div>
                </div>
              </div>
              <div ref="heroArtEl" class="hero-art">
                <AvatarPanel
                  :speaking="speaking"
                  :paused="paused"
                  :line="currentLine || `你好，我是知知。`"
                  :supported="supported"
                  section-label="首页"
                  @play="speakText(`欢迎回来。今天我们学${homeContinue.title}。`)"
                  @pause="onPause"
                  @resume="onResume"
                  @stop="stop"
                  @prev="() => {}"
                  @next="() => {}"
                />
              </div>
            </section>
          </div>
        </template>

        <!-- CATALOG -->
        <template v-else-if="view === 'catalog'">
          <div class="catalog-head">
            <h1 class="h1">课程知识点目录</h1>
          </div>

          <div class="lecture-entry-block card">
            <div class="lecture-entry-head">
              <div>
                <h2 class="h2" style="margin: 0">课件讲解</h2>
              </div>
            </div>
            <div class="lecture-entry-grid">
              <button
                v-for="lec in lectureEntries"
                :key="lec.id"
                type="button"
                class="lecture-entry"
                @click="openClassroom(lec.id)"
              >
                <span class="lecture-entry-title">{{ lec.title }}</span>
                <span class="lecture-entry-meta">{{ lec.deckTitle }} · {{ lec.slideCount }} 页</span>
                <span class="lecture-entry-go">打开课件 →</span>
              </button>
            </div>
          </div>

          <div class="catalog-topics-head">
            <h2 class="h2">知识点</h2>
            <div class="search">
              <span>⌕</span>
              <input v-model="search" placeholder="搜索知识点..." aria-label="搜索知识点" />
            </div>
          </div>

          <div class="catalog-layout">
            <aside class="card chapter-panel">
              <div class="chapter-title">知识点框架</div>
              <button
                class="chapter-btn"
                :class="{ active: chapterFilter === 'all' }"
                type="button"
                @click="selectChapterFilter('all')"
              >
                <span>全部知识点</span><span class="tiny">{{ flatTopics.length }}</span>
              </button>
              <div v-for="ch in chapters" :key="'cat-' + ch.id" class="catalog-tree-ch">
                  <button
                  class="chapter-btn catalog-tree-summary"
                  :class="{ active: chapterFilter === ch.id }"
                  type="button"
                  @click="selectChapterFilter(ch.id)"
                >
                  <span
                    class="outline-caret catalog-caret"
                    :class="{ open: outlineOpen[ch.id] }"
                    @click.stop="toggleOutline(ch.id)"
                  >›</span>
                  <span>{{ ch.title }}</span>
                </button>
                <div v-show="outlineOpen[ch.id]" class="catalog-tree-topics">
                  <button
                    v-if="hasLectureDeck(ch.id)"
                    class="catalog-tree-topic ppt"
                    type="button"
                    @click="openClassroom(ch.id)"
                  >
                    本讲课件讲解 →
                  </button>
                  <button
                    v-for="t in ch.topics"
                    :key="'cat-t-' + t.id"
                    class="catalog-tree-topic"
                    :class="{ current: activeTopicId === t.id && view === 'lesson' }"
                    type="button"
                    @click="openTopic(t.id)"
                  >
                    {{ t.title }}
                  </button>
                </div>
              </div>
            </aside>
            <div class="topic-grid">
              <article v-for="t in filteredTopics" :key="t.id" class="card topic-card">
                <div class="topic-card-top">
                  <span class="pill">{{ t.type }}</span>
                </div>
                <div class="tiny" style="margin-top: 10px">{{ t.chapterTitle }}</div>
                <h3>{{ t.title }}</h3>
                <p>{{ t.desc }}</p>
                <div class="progress-track" v-if="store.progress[t.id]">
                  <div class="progress-fill" :style="{ width: Math.min(100, ((store.progress[t.id].section || 0) + 1) * 25) + '%' }" />
                </div>
                <div class="topic-card-footer">
                  <span class="tiny">{{ store.progress[t.id] ? "继续学习" : "尚未开始" }}</span>
                  <button class="btn btn-primary btn-small" type="button" @click="openTopic(t.id)">
                    {{ t.status === "ready" ? "开始学习" : "查看占位" }}
                  </button>
                </div>
              </article>
            </div>
          </div>
        </template>

        <!-- LESSON -->
        <template v-else-if="view === 'lesson'">
          <div class="workspace-header">
            <div>
              <div class="eyebrow">{{ current?.chapter?.title }}</div>
              <h1 class="h1">{{ current?.topic?.title }}</h1>
            </div>
            <button class="btn" type="button" @click="go('catalog')">返回目录</button>
          </div>

          <div v-if="!topicReady" class="card" style="padding: 24px">
            <h3>该知识点内容建设中</h3>
            <button class="btn btn-primary" type="button" @click="go('catalog')">去知识点目录</button>
          </div>

          <div v-else class="workspace-main">
            <section class="card lesson-card">
              <div class="lesson-top">
                <span class="tiny">{{ section === 0 ? "讲解" : "做题答疑" }}</span>
              </div>
              <div class="step-list two-steps">
                <button
                  v-for="(name, i) in lessonParts"
                  :key="name"
                  class="step"
                  :class="{ active: section === i, done: section > i }"
                  type="button"
                  @click="gotoSection(i, { speak: false })"
                >
                  <span class="num">{{ i + 1 }}</span>{{ name }}
                </button>
              </div>

              <!-- 讲解：知识库正文为主，提纲为辅，案例跟做 -->
              <div class="lesson-body" v-if="section === 0">
                <h2>{{ current.topic.title }}</h2>
                <template v-if="overviewStory.length">
                  <p v-for="(para, i) in overviewStory" :key="'intro-' + i" class="intro-plain">{{ para }}</p>
                </template>
                <p v-else class="intro-plain">{{ current.topic.desc }}</p>

                <h3 class="teach-h3">讲解正文</h3>
                <LessonReadingPanel
                  :sections="lessonReading"
                  :notes="topicNotes"
                  :source="lessonReadingSource"
                  :create-note="createLessonNote"
                  empty-hint="讲义暂未加载"
                  @reload="loadTopicAssets"
                />
                <div v-if="topicNotes.length" class="topic-notes-mini">
                  <button class="btn btn-small btn-soft" type="button" @click="reviewTab = 'notes'; go('review')">
                    标注 {{ topicNotes.length }}
                  </button>
                </div>

                <details class="outline-fold" open>
                  <summary>本讲提纲（步骤卡）</summary>
                  <template v-if="overviewDetails.length">
                    <div v-for="(d, i) in overviewDetails" :key="'d-' + i" class="outline-block">
                      <b>{{ i + 1 }}. {{ d.title }}</b>
                      <ul>
                        <li v-for="(p, j) in d.points || []" :key="j">{{ p }}</li>
                      </ul>
                    </div>
                  </template>
                  <ol v-else>
                    <li v-for="(s, i) in stepCard?.steps || []" :key="i">{{ s }}</li>
                  </ol>
                  <div v-if="Object.keys(stepCard?.symbols || {}).length" class="symbol-row">
                    <span v-for="(v, k) in stepCard.symbols" :key="k" class="symbol-chip">
                      <b>{{ k }}</b> {{ v }}
                    </span>
                  </div>
                  <div class="formula" style="margin-top: 12px">
                    <small>{{ hint.formulaLabel }}</small>
                    {{ hint.formula }}
                  </div>
                </details>

                <template v-if="activeCase">
                  <h3 class="teach-h3">例题跟做</h3>
                  <div class="case-tools">
                    <div>
                      <div class="case-title">{{ activeCase.title }}</div>
                      <div class="tiny" style="margin-top: 5px">{{ activeCase.intro }}</div>
                    </div>
                    <button
                      v-if="topicCases.length > 1"
                      class="btn btn-small btn-soft"
                      type="button"
                      @click="changeCase"
                    >
                      换个情境
                    </button>
                  </div>
                  <div style="margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap">
                    <button
                      v-if="isWalkthroughCase"
                      class="btn btn-primary"
                      type="button"
                      @click="runCaseWalkthrough"
                    >
                      展开案例
                    </button>
                    <button
                      v-else
                      class="btn btn-primary"
                      type="button"
                      :disabled="computeLoading"
                      @click="runCaseCompute"
                    >
                      {{ computeLoading ? "计算中…" : "程序验算" }}
                    </button>
                  </div>
                  <p class="err" v-if="computeError">{{ computeError }}</p>
                  <div class="concept-box" v-if="isWalkthroughCase && caseBrief" style="margin-top: 12px">
                    <h4>案例拆解</h4>
                    <p v-if="caseBrief.takeaway">要点：<b>{{ caseBrief.takeaway }}</b></p>
                    <div class="panel-md" v-html="renderRichText(caseBrief.panel, { math: true })" />
                  </div>
                  <div class="concept-box" v-if="!isWalkthroughCase && computeResult" style="margin-top: 12px">
                    <h4>验算结果</h4>
                    <p>最优方案：<b>{{ computeResult.best }}</b>（{{ computeResult.best_value }}）</p>
                    <div
                      class="panel-md"
                      v-html="renderRichText(computeResult.panel_markdown, { math: true })"
                    />
                  </div>
                </template>

                <div class="exit-teach">
                  <button class="btn" type="button" @click="playSection">听本讲口播</button>
                  <button class="btn btn-primary" type="button" @click="gotoSection(1)">
                    结束讲解，去做小测答疑
                  </button>
                </div>
              </div>

              <!-- 做题答疑：小测 + 追问 -->
              <div class="lesson-body" v-else>
                <h2>做题答疑</h2>

                <h3 class="teach-h3">小测</h3>
                <p class="tiny" v-if="choiceQuizzes.length">
                  {{ (quizIndex % choiceQuizzes.length) + 1 }} / {{ choiceQuizzes.length }}
                </p>
                <div class="quiz" v-if="currentQuiz?.type === 'choice'">
                  <h3 style="font-size: 15px; line-height: 1.8">{{ currentQuiz.question }}</h3>
                  <label
                    v-for="(text, key) in currentQuiz.options"
                    :key="key"
                    class="option"
                    :class="{
                      selected: quizChoice === key,
                      correct: quizChecked && key === currentQuiz.answer,
                      incorrect: quizChecked && quizChoice === key && key !== currentQuiz.answer,
                    }"
                  >
                    <input type="radio" :value="key" v-model="quizChoice" :disabled="quizChecked" />
                    <b>{{ key }}</b> {{ text }}
                  </label>
                  <div v-if="quizChecked" class="feedback" :class="quizFeedback?.correct ? 'good' : 'bad'">
                    <b>{{ quizFeedback?.correct ? "回答正确" : "本题需要再巩固" }}</b><br />
                    {{ quizFeedback?.reason }}
                  </div>
                  <div v-if="!quizChecked" style="display: flex; gap: 8px; flex-wrap: wrap">
                    <button class="btn btn-primary" type="button" @click="submitQuiz">提交答案</button>
                    <button class="btn" type="button" @click="openAsk(sectionAskPreset())">先追问再作答</button>
                  </div>
                  <div v-else style="display: flex; gap: 8px; flex-wrap: wrap">
                    <button v-if="!quizFeedback?.correct" class="btn btn-primary" type="button" @click="reteachWrong">
                      返回讲解重听
                    </button>
                    <button class="btn" type="button" @click="resetQuiz">重做本题</button>
                    <button
                      v-if="choiceQuizzes.length > 1"
                      class="btn btn-soft"
                      type="button"
                      @click="nextQuiz"
                    >
                      下一题
                    </button>
                  </div>
                </div>
                <div v-else class="empty">暂无选择题</div>

                <h3 class="teach-h3">答疑</h3>
                <section class="ask-inline ask-inline-open">
                  <div class="ask-suggest-row">
                    <button v-for="q in askSuggestions" :key="q" class="chip" type="button" @click="question = q">
                      {{ q }}
                    </button>
                  </div>
                  <div class="chatlog ask-log">
                    <div v-for="(m, i) in chat" :key="i" class="message" :class="{ mine: m.role === 'user' }">
                      <div class="msg-icon">{{ m.role === "user" ? "我" : "知" }}</div>
                      <div>
                        <div
                          class="msg-content"
                          v-html="renderRichText(m.text, { math: m.role !== 'user' })"
                        />
                        <div class="msg-meta">{{ m.role === "user" ? "学生" : m.topic || "课程回答" }}</div>
                        <div v-if="m.sources?.length" class="msg-sources">
                          教材来源：
                          <span v-for="(s, si) in m.sources" :key="si">{{ s.source }}{{ s.title ? " · " + s.title : "" }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="composer-box">
                    <textarea v-model="question" rows="2" :placeholder="'针对「' + current.topic.title + '」追问…'" />
                    <div class="composer-footer">
                      <button class="btn btn-small" type="button" @click="gotoSection(0, { speak: false })">
                        返回讲解
                      </button>
                      <button class="btn btn-primary btn-small" type="button" :disabled="askLoading || !backendOk" @click="doAsk">
                        {{ askLoading ? "生成中…" : "发送" }}
                      </button>
                    </div>
                  </div>
                  <p class="err" v-if="askError">{{ askError }}</p>
                  <button v-if="askResult" class="btn btn-soft btn-small" style="margin-top: 8px" type="button" @click="speakAsk">
                    口播回答
                  </button>
                </section>
              </div>

              <div class="coach-bar">
                <div class="coach-actions">
                  <button
                    v-if="coach.primary.run !== 'noop'"
                    class="btn btn-primary btn-small"
                    type="button"
                    @click="runCoach(coach.primary.run)"
                  >
                    {{ coach.primary.label }}
                  </button>
                  <button
                    v-for="s in coach.secondary"
                    :key="s.run + s.label"
                    class="btn btn-small"
                    type="button"
                    @click="runCoach(s.run)"
                  >
                    {{ s.label }}
                  </button>
                </div>
              </div>
            </section>

            <AvatarPanel
              class="avatar-panel"
              :speaking="speaking"
              :paused="paused"
              :line="currentLine"
              :supported="supported"
              :section-label="sessionLabel"
              @play="playSection"
              @pause="onPause"
              @resume="onResume"
              @stop="stop"
              @prev="prevSection"
              @next="nextSection"
            />
          </div>
        </template>

        <!-- REVIEW -->
        <template v-else>
          <h1 class="h1">复习与记录</h1>
          <div class="review-grid">
            <div class="card review-main">
              <div class="tabs">
                <button class="tab" :class="{ active: reviewTab === 'summary' }" type="button" @click="reviewTab = 'summary'">
                  知识点速览
                </button>
                <button class="tab" :class="{ active: reviewTab === 'wrong' }" type="button" @click="reviewTab = 'wrong'">
                  历史错题 ({{ store.wrong.length }})
                </button>
                <button class="tab" :class="{ active: reviewTab === 'notes' }" type="button" @click="reviewTab = 'notes'; refreshAllNotes()">
                  我的标注 ({{ noteCount }})
                </button>
              </div>
              <div v-if="reviewTab === 'summary'">
                <div class="concept-box" v-for="t in readyTopics()" :key="t.id" style="margin-bottom: 12px">
                  <h4>{{ t.title }}</h4>
                  <button class="btn btn-small btn-soft" style="margin-top: 8px" type="button" @click="openTopic(t.id)">
                    进入
                  </button>
                </div>
              </div>
              <div v-else-if="reviewTab === 'wrong'">
                <div v-if="!store.wrong.length" class="empty">暂无错题</div>
                <div v-for="(w, i) in store.wrong.slice().reverse()" :key="i" class="wrong-item">
                  <div class="tiny">{{ new Date(w.date).toLocaleString("zh-CN") }}</div>
                  <h4>{{ w.question }}</h4>
                  <p>你的回答：{{ w.chosen }}</p>
                  <p>正确答案：{{ w.correct }}</p>
                  <p>{{ w.reason }}</p>
                  <button class="btn btn-small btn-soft" type="button" @click="openWrongReteach(w)">
                    回到该讲并按步骤重讲
                  </button>
                </div>
              </div>
              <div v-else>
                <div v-if="notesLoading" class="empty">标注加载中…</div>
                <div v-else-if="!allNotes.length" class="empty">暂无标注</div>
                <div v-for="n in allNotes" :key="n.id" class="note-item">
                  <div class="note-head">
                    <span class="note-swatch" :class="n.color || 'amber'" />
                    <span class="pill purple" v-if="n.tag">{{ n.tag }}</span>
                    <span class="tiny">{{ noteTopicTitle(n.method_id) }}</span>
                    <span class="tiny">{{ new Date(n.created_at * 1000).toLocaleString("zh-CN") }}</span>
                  </div>
                  <blockquote>「{{ n.quote }}」</blockquote>
                  <p v-if="n.remark" class="note-remark">{{ n.remark }}</p>
                  <div class="note-actions">
                    <button class="btn btn-small btn-soft" type="button" @click="openNoteTarget(n)">回到原文</button>
                    <button class="btn btn-small" type="button" @click="removeNote(n.id)">删除</button>
                  </div>
                </div>
              </div>
            </div>
            <aside class="card review-detail">
              <h3>学习数据</h3>
              <p class="compact">账号：{{ user?.username }}</p>
              <p class="compact">已进入知识点：{{ numLearned() }}</p>
              <p class="compact">错题数：{{ store.wrong.length }}</p>
              <p class="compact">标注数：{{ noteCount }}</p>
            </aside>
          </div>
        </template>
      </div>
    </main>

    <nav class="m-bottom-nav mobile-only" aria-label="手机底部导航">
      <button type="button" class="m-bottom-item" :class="{ active: view === 'home' }" @click="go('home')">
        <span class="m-ico">⌂</span>
        <span>首页</span>
      </button>
      <button
        type="button"
        class="m-bottom-item"
        :class="{ active: view === 'catalog' || (view === 'lesson' && !askOpen) }"
        @click="go('catalog')"
      >
        <span class="m-ico">书</span>
        <span>课程</span>
      </button>
      <button type="button" class="m-bottom-item" :class="{ active: view === 'qa' }" @click="openQaSpace()">
        <span class="m-ico">问</span>
        <span>答疑</span>
      </button>
      <button
        type="button"
        class="m-bottom-item"
        :class="{ active: view === 'review' }"
        @click="go('review')"
      >
        <span class="m-ico">记</span>
        <span>记录</span>
      </button>
    </nav>
  </div>

  <SpiritFloat
    :visible="spiritFloatVisible"
    :context-id="view === 'classroom' && activeDeck ? activeDeck.topicId : store.lastTopicId || activeTopicId || 'expected_value'"
    :backend-ok="backendOk"
    :external-speaking="view === 'classroom' ? classroomSpeaking : speaking"
    :external-paused="view === 'classroom' ? false : paused"
    :external-line="view === 'classroom' ? classroomLine : currentLine"
    :bottom-pad="72"
    @open-qa="openQaSpace"
    @open-topic="(id) => openTopic(id)"
    @stop-external="stopSpiritExternal"
  />
  </template>
</template>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 272px;
  background: #18263f;
  color: #dbdeef;
  min-height: 100vh;
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 24px 14px 16px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  transition: width 0.2s ease;
}
.sidebar.collapsed {
  width: 76px;
  padding: 20px 10px 14px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 2px 4px 18px 10px;
  color: #fff;
  position: relative;
}
.sidebar.collapsed .brand {
  flex-direction: column;
  gap: 10px;
  padding: 2px 0 14px;
}
.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: #cfeee3;
  color: #18263f;
  display: grid;
  place-items: center;
  font-weight: 900;
  flex-shrink: 0;
}
.brand-copy {
  min-width: 0;
  flex: 1;
}
.sidebar.collapsed .brand-copy {
  display: none;
}
.brand-text {
  font-weight: 850;
  font-size: 18px;
}
.brand-sub {
  color: #92a7b2;
  font-size: 10px;
  letter-spacing: 0.12em;
}
.sidebar-toggle {
  width: 28px;
  height: 28px;
  border: 1px solid #40516a;
  border-radius: 8px;
  background: #24364f;
  color: #cfeee3;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
  display: grid;
  place-items: center;
}
.sidebar-toggle:hover {
  background: #304560;
  color: #fff;
}
.nav-caption {
  font-size: 11px;
  letter-spacing: 2px;
  color: #8188a7;
  padding: 4px 12px 8px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 11px 14px;
  border: 0;
  background: transparent;
  color: #b6c8d0;
  border-radius: 12px;
  text-align: left;
  font-weight: 650;
  margin: 2px 0;
}
.nav-short {
  display: none;
  width: 100%;
  text-align: center;
  font-weight: 800;
}
.nav-label {
  min-width: 0;
}
.sidebar.collapsed .nav-item {
  padding: 12px 0;
  justify-content: center;
}
.sidebar.collapsed .nav-short {
  display: block;
}
.sidebar.collapsed .nav-label {
  display: none;
}
.nav-item:hover {
  background: #304560;
  color: #fff;
}
.nav-item.active {
  background: #304560;
  color: #fff;
}
.outline-caret {
  display: inline-block;
  color: #a8d9cc;
  font-size: 16px;
  line-height: 1;
  transition: transform 0.2s;
  flex-shrink: 0;
  margin-top: 1px;
}
.outline-caret.open {
  transform: rotate(90deg);
}
.sidebar-bottom {
  flex-shrink: 0;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #40516a;
}
.sidebar.collapsed .sidebar-bottom {
  padding-top: 10px;
}
.sidebar.collapsed .user-meta {
  display: none;
}
.sidebar.collapsed .user-mini {
  justify-content: center;
}
.boot-screen {
  min-height: 100vh;
  display: grid;
  place-items: center;
  color: #6b7290;
  background: #f4f5fb;
}
.logout-link {
  border: 0;
  background: none;
  color: #9aa3c7;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  font-size: inherit;
}
.topic-notes-mini {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.lecture-entry-block {
  padding: 18px 18px 14px;
  margin: 18px 0 20px;
}
.lecture-entry-head {
  margin-bottom: 12px;
}
.lecture-entry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}
.lecture-entry {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  text-align: left;
  border: 1px solid #e8ebf5;
  background: #fbfbfd;
  border-radius: 14px;
  padding: 14px 14px 12px;
  cursor: pointer;
  color: inherit;
}
.lecture-entry:hover {
  border-color: #c5befa;
  background: #f8f6ff;
}
.lecture-entry-title {
  font-size: 13px;
  font-weight: 800;
  line-height: 1.45;
}
.lecture-entry-meta {
  font-size: 11px;
  color: #8a91ab;
}
.lecture-entry-go {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 800;
  color: #6658df;
}
.clickable-stat {
  cursor: pointer;
}
.clickable-stat:hover {
  outline: 1px solid rgba(102, 88, 223, 0.25);
}
.note-item {
  border: 1px solid #e8ebf5;
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 12px;
  background: #fbfbfd;
}
.note-head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.note-swatch {
  width: 12px;
  height: 12px;
  border-radius: 999px;
}
.note-swatch.amber {
  background: #f6d56a;
}
.note-swatch.mint {
  background: #7ddec0;
}
.note-swatch.rose {
  background: #f3a6b5;
}
.note-swatch.sky {
  background: #8ec5f5;
}
.note-item blockquote {
  margin: 0;
  color: #24253b;
  line-height: 1.7;
  font-size: 14px;
}
.note-remark {
  margin: 8px 0 0;
  color: #6b7290;
  font-size: 13px;
}
.note-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.user-mini {
  display: flex;
  gap: 9px;
  align-items: center;
  padding: 18px 5px 0;
  font-size: 12px;
}
.user-icon {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #e7ddff;
  color: #544ba7;
  font-weight: 800;
}
.user-mini small {
  display: block;
  color: #848cac;
}
.main {
  flex: 1;
  min-width: 0;
}
.topbar {
  height: 78px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 38px;
  background: rgba(255, 255, 255, 0.88);
  border-bottom: 1px solid #e9eaf1;
  position: sticky;
  top: 0;
  z-index: 4;
  backdrop-filter: blur(12px);
}
.breadcrumb {
  font-size: 13px;
  font-weight: 650;
  color: #686f85;
}
.top-tag {
  background: #effaf7;
  color: #287d71;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 800;
  padding: 8px 12px;
}
.content {
  max-width: 1510px;
  padding: 36px 42px 80px;
  margin: auto;
}
.content.home-mode {
  height: calc(100dvh - 78px);
  max-height: calc(100dvh - 78px);
  padding: 24px 42px 28px;
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.home-screen {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.home-screen .hero {
  flex: 1;
  min-height: 0;
}
.home-screen .hero-art {
  min-height: 0;
}
.eyebrow {
  font-size: 12px;
  letter-spacing: 1.5px;
  font-weight: 800;
  color: var(--primary);
  margin-bottom: 9px;
}
.h1 {
  font-size: 31px;
  font-weight: 850;
  margin: 0;
  line-height: 1.32;
}
.h2 {
  font-size: 21px;
  font-weight: 820;
  margin: 0;
}
.sub {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.8;
  margin: 10px 0 0;
}
.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid #e4e5ef;
  border-radius: 12px;
  padding: 11px 16px;
  background: #fff;
  color: #454b66;
  font-size: 13px;
  font-weight: 750;
}
.btn-primary {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}
.btn-soft {
  background: var(--primary-soft);
  border-color: #e9e4ff;
  color: var(--primary);
}
.btn-small {
  font-size: 12px;
  padding: 8px 11px;
}
.pill {
  display: inline-flex;
  border-radius: 30px;
  padding: 5px 9px;
  background: #f4f5fa;
  color: #686f84;
  font-size: 11px;
  font-weight: 750;
}
.pill.purple {
  background: var(--primary-soft);
  color: var(--primary);
}
.pill.green {
  background: #e6f8f0;
  color: #158a65;
}
.pill.amber {
  background: #fff3d9;
  color: #b37a19;
}
.hero {
  min-height: 360px;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(ellipse 70% 80% at 12% 20%, rgba(185, 223, 211, 0.85), transparent 55%),
    radial-gradient(ellipse 55% 60% at 88% 78%, rgba(207, 232, 220, 0.7), transparent 50%),
    linear-gradient(145deg, #e7f1ea 0%, #f2f6f1 48%, #ddece4 100%);
  border: 1px solid #d5e6db;
  border-radius: 28px;
  padding: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(320px, 0.88fr);
  gap: 0;
}
.hero-glow {
  position: absolute;
  width: 280px;
  height: 280px;
  right: 18%;
  top: -60px;
  border-radius: 50%;
  background: rgba(155, 201, 186, 0.35);
  filter: blur(40px);
  pointer-events: none;
  animation: heroFloat 7s ease-in-out infinite;
}
@keyframes heroFloat {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(18px);
  }
}
.hero-copy {
  max-width: none;
  position: relative;
  z-index: 1;
  padding: clamp(32px, 4.5vw, 64px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  animation: heroRise 0.7s ease both;
}
@keyframes heroRise {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.hero-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 22px;
}
.hero-mark {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  background: #18263f;
  color: #cfeee3;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 18px;
  box-shadow: 0 12px 28px rgba(24, 38, 63, 0.16);
}
.hero-brand strong {
  font-size: 20px;
  font-weight: 900;
  color: #18263f;
  letter-spacing: -0.02em;
}
.hero-eyebrow {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: #166c62;
  margin: 0 0 8px;
  animation: heroRise 0.75s ease 0.08s both;
}
.hero h1 {
  font-size: clamp(30px, 3.4vw, 44px);
  line-height: 1.28;
  margin: 0 0 14px;
  font-weight: 900;
  color: #18263f;
  letter-spacing: -0.03em;
  max-width: 14em;
  animation: heroRise 0.8s ease 0.12s both;
}
.hero-buttons {
  display: flex;
  gap: 12px;
  margin-top: 28px;
  flex-wrap: wrap;
  align-items: flex-start;
  animation: heroRise 0.9s ease 0.24s both;
}
.hero-continue {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-start;
}
.hero-continue-from {
  font-size: 12px;
  color: #5f7a72;
  font-weight: 650;
  line-height: 1.4;
  max-width: 22em;
}
.hero-buttons .btn-primary {
  background: #18263f;
  border-color: #18263f;
}
.hero-buttons .btn-primary:hover {
  background: #24364f;
}
.hero-art {
  width: auto;
  position: relative;
  z-index: 1;
  min-height: 360px;
  background:
    radial-gradient(circle at 55% 32%, rgba(185, 223, 211, 0.95) 0%, rgba(213, 234, 225, 0.55) 46%, transparent 78%);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
  gap: 12px;
  padding: 28px 24px;
  animation: heroRise 0.85s ease 0.16s both;
}
.hero-art :deep(.avatar-panel) {
  background: rgba(255, 255, 255, 0.82);
  border-color: rgba(213, 232, 223, 0.9);
  box-shadow: 0 18px 48px rgba(24, 38, 63, 0.1);
  backdrop-filter: blur(8px);
}
.hero-art :deep(.avatar-scene) {
  height: min(38vh, 280px);
}
.section-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin: 32px 0 17px;
}
.section-label {
  font-size: 12px;
  color: var(--muted);
}
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.stat {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 15px;
  padding: 20px;
}
.stat-num {
  font-size: 29px;
  font-weight: 850;
  margin: 6px 0;
}
.dim {
  font-size: 14px;
  color: #a2a5b5;
}
.stat-label {
  font-size: 12px;
  color: #838aa1;
}
.stat-note {
  font-size: 11px;
  color: #acaec0;
}
.three-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}
.feature-card {
  padding: 23px;
}
.feature-icon {
  width: 47px;
  height: 47px;
  display: grid;
  place-items: center;
  border-radius: 15px;
  margin-bottom: 16px;
  font-weight: 850;
}
.feature-icon.purple {
  background: #eeeaff;
  color: #6a57db;
}
.feature-icon.mint {
  background: #dff8f2;
  color: #228879;
}
.feature-icon.orange {
  background: #fff1dc;
  color: #d39435;
}
.feature-card p {
  color: #83899c;
  font-size: 12px;
  line-height: 1.8;
}
.catalog-head {
  display: flex;
  gap: 20px;
  justify-content: space-between;
  align-items: flex-start;
}
.catalog-topics-head {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  align-items: center;
  margin: 22px 0 14px;
  flex-wrap: wrap;
}
.catalog-topics-head .h2 {
  margin: 0;
}
.search {
  height: 44px;
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 13px;
  min-width: 255px;
}
.search input {
  border: 0;
  outline: 0;
  width: 100%;
  background: transparent;
}
.catalog-layout {
  display: grid;
  grid-template-columns: 270px minmax(0, 1fr);
  gap: 20px;
  margin-top: 0;
}
.chapter-panel {
  padding: 14px;
  height: max-content;
  position: sticky;
  top: 90px;
}
.chapter-title {
  font-size: 12px;
  font-weight: 780;
  color: #878ca1;
  padding: 10px;
}
.chapter-btn {
  display: flex;
  width: 100%;
  border: 0;
  border-radius: 11px;
  background: none;
  padding: 13px;
  text-align: left;
  font-weight: 700;
  font-size: 13px;
  color: #5a6178;
  gap: 8px;
}
.chapter-btn span:first-child {
  flex: 1;
}
.chapter-btn.active {
  color: #12594f;
  background: #e0f0e7;
}
.catalog-tree-ch {
  border-bottom: 1px solid #eef1ef;
}
.catalog-tree-summary {
  align-items: flex-start;
}
.catalog-caret {
  color: #166c62;
  margin-right: 2px;
  margin-top: 2px;
}
.catalog-tree-topics {
  display: grid;
  gap: 2px;
  padding: 0 4px 10px 18px;
}
.catalog-tree-topic {
  border: 0;
  background: transparent;
  text-align: left;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  color: #5a6178;
  line-height: 1.4;
}
.catalog-tree-topic:hover {
  background: #f0f4ef;
  color: #12594f;
}
.catalog-tree-topic.current {
  background: #dcefe6;
  color: #12594f;
  font-weight: 750;
}
.catalog-tree-topic.ppt {
  color: #166c62;
  font-weight: 750;
}
.topic-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.topic-card {
  padding: 23px;
  min-height: 215px;
  display: flex;
  flex-direction: column;
}
.topic-card-top {
  display: flex;
  justify-content: space-between;
}
.topic-card h3 {
  font-size: 17px;
  margin: 8px 0;
}
.topic-card p {
  font-size: 12px;
  color: #8d94a8;
  line-height: 1.75;
  margin: 0 0 18px;
}
.topic-card-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.progress-track {
  height: 6px;
  background: #f0f0f8;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #7b70f0, #57c2b4);
}
.workspace-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 21px;
}
.workspace-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 20px;
  align-items: start;
}
.lesson-card {
  padding: 27px;
  min-height: 540px;
}
.lesson-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.step-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 22px 0 24px;
}
.step-list.two-steps .step {
  flex: 1;
  min-width: 140px;
  justify-content: center;
}
.teach-h3 {
  margin: 22px 0 8px;
  font-size: 16px;
  color: #2a3148;
}
.lesson-article {
  margin: 12px 0 18px;
  padding: 16px 18px;
  border: 1px solid #e7ebf4;
  border-radius: 14px;
  background: #fbfcff;
}
.lesson-article h4 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #24324d;
}
.lesson-md {
  color: #3d465c;
  font-size: 14px;
  line-height: 1.85;
}
.lesson-md :deep(.md-h) {
  margin: 14px 0 8px;
  color: #2a3148;
}
.lesson-md :deep(.md-p) {
  margin: 0 0 10px;
}
.lesson-md :deep(.md-ul) {
  margin: 0 0 12px;
  padding-left: 1.2em;
}
.lesson-md :deep(.md-table-wrap) {
  overflow-x: auto;
  margin: 12px 0 14px;
  border: 1px solid #e2e7f2;
  border-radius: 12px;
  background: #fff;
}
.lesson-md :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.lesson-md :deep(.md-table th),
.lesson-md :deep(.md-table td) {
  border-bottom: 1px solid #e8ecf4;
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
  line-height: 1.55;
  color: #3d465c;
}
.lesson-md :deep(.md-table th) {
  background: #f3f6fb;
  color: #24324d;
  font-weight: 750;
}
.lesson-md :deep(.md-table tr:last-child td) {
  border-bottom: 0;
}
.lesson-md :deep(.md-arrow) {
  margin: 0 4px;
  color: #5b6f96;
  font-weight: 700;
}
.lesson-md :deep(.md-hr) {
  border: 0;
  border-top: 1px dashed #d9deea;
  margin: 14px 0;
}
.outline-fold {
  margin: 18px 0 8px;
  border: 1px dashed #d9deea;
  border-radius: 12px;
  padding: 10px 14px 12px;
  background: #f7f8fc;
}
.outline-fold summary {
  cursor: pointer;
  font-weight: 750;
  color: #3d4a66;
  font-size: 13px;
}
.outline-block {
  margin-top: 10px;
  font-size: 13px;
  color: #4a556c;
}
.outline-block ul {
  margin: 4px 0 0;
  padding-left: 1.2em;
}
.symbol-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.symbol-chip {
  font-size: 11px;
  background: #fff;
  border: 1px solid #e2e7f2;
  border-radius: 999px;
  padding: 4px 9px;
  color: #52607a;
}
.symbol-chip b {
  color: #2f3d5c;
  margin-right: 4px;
}
.exit-teach {
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid #eceef5;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.ask-inline-open {
  margin-top: 8px;
  padding-top: 0;
  border-top: 0;
}
.step {
  display: flex;
  align-items: center;
  gap: 7px;
  background: #f7f7fb;
  color: #9095a8;
  border: 1px solid #edecf5;
  padding: 9px 11px;
  border-radius: 11px;
  font-size: 12px;
  font-weight: 700;
}
.step.active {
  background: var(--primary-soft);
  border-color: #dcd6ff;
  color: var(--primary);
}
.step.done {
  color: #438c83;
  background: #effaf7;
}
.step .num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #fff;
  font-size: 10px;
}
.lesson-body h2 {
  font-size: 25px;
  margin: 5px 0 14px;
}
.lesson-body p {
  line-height: 1.95;
  color: #5b637d;
  font-size: 14px;
}
.intro-plain {
  margin: 0 0 10px;
  line-height: 1.75;
  color: #3d4458;
  font-size: 15px;
}
.concept-box {
  background: linear-gradient(135deg, #f7f5ff, #fafbff);
  border: 1px solid #e9e6ff;
  border-left: 4px solid var(--primary);
  border-radius: 14px;
  padding: 20px;
  margin: 20px 0;
}
.concept-box h4 {
  margin: 0 0 9px;
  color: #5249ac;
}
.formula {
  background: #262942;
  color: #fff;
  border-radius: 14px;
  padding: 19px 20px;
  margin: 18px 0;
  white-space: pre-line;
  line-height: 1.7;
  font-size: 13.5px;
}
.formula small {
  display: block;
  color: #b9bcdb;
  font-size: 11px;
  margin-bottom: 7px;
}
.case-tools {
  display: flex;
  justify-content: space-between;
  gap: 9px;
  margin: 16px 0;
  flex-wrap: wrap;
}
.case-title {
  font-weight: 820;
  font-size: 16px;
}
.help-note {
  padding: 11px 13px;
  background: #fff9ed;
  color: #a57e31;
  border: 1px solid #ffeed2;
  border-radius: 11px;
  font-size: 11px;
  line-height: 1.8;
}
.teach-actions {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  border-top: 1px solid #eff0f5;
  margin-top: 26px;
  padding-top: 19px;
  flex-wrap: wrap;
}
.session-chip {
  margin: 14px 8px 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: #1c1d30;
  color: #e8eaf8;
  font-size: 12px;
  line-height: 1.6;
}
.session-chip strong {
  display: block;
  font-size: 13px;
  margin-top: 4px;
}
.source-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.coach-bar {
  margin-top: 22px;
  padding: 16px 18px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f4f1ff, #eefbf7);
  border: 1px solid #e4e0ff;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.coach-tip {
  font-size: 13px;
  color: #4f5670;
  margin-top: 4px;
  font-weight: 650;
}
.coach-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.ask-inline {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px dashed #e4e6f0;
}
.ask-log {
  max-height: 240px;
  padding: 8px 0 12px;
}
.ask-suggest-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.chip {
  border: 1px solid #e6e7f2;
  background: #fff;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 11px;
  color: #5b6280;
}
.msg-sources {
  margin-top: 6px;
  font-size: 11px;
  color: #6b5fad;
  line-height: 1.6;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.avatar-panel {
  position: sticky;
  top: 100px;
}
.quiz {
  background: #fbfbff;
  border: 1px solid #ebebf5;
  border-radius: 16px;
  padding: 21px;
}
.option {
  display: flex;
  align-items: center;
  gap: 11px;
  border: 1px solid #e6e8f1;
  background: #fff;
  border-radius: 11px;
  padding: 12px 14px;
  margin: 9px 0;
  cursor: pointer;
  font-size: 13px;
}
.option.selected {
  border-color: #887bff;
  background: #f4f1ff;
}
.option.correct {
  border-color: #52b996;
  background: #e9faf3;
}
.option.incorrect {
  border-color: #eaa18c;
  background: #fff3ef;
}
.option input {
  width: auto !important;
  margin: 0 !important;
  accent-color: var(--primary);
}
.feedback {
  border-radius: 12px;
  padding: 14px 16px;
  font-size: 12px;
  line-height: 1.8;
  margin: 12px 0;
}
.feedback.good {
  background: #eafbf3;
  color: #2b7b5e;
}
.feedback.bad {
  background: #fff2ec;
  color: #a65c42;
}
.qa-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  margin-top: 24px;
}
.chat-card {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 620px;
}
.chat-head {
  border-bottom: 1px solid var(--border);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 11px;
}
.chatlog {
  padding: 26px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 420px;
  overflow-y: auto;
}
.message {
  display: flex;
  gap: 10px;
  max-width: 94%;
}
.message.mine {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.msg-icon {
  height: 31px;
  width: 31px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: #efedff;
  color: #6758cf;
  font-size: 12px;
  font-weight: 850;
}
.message.mine .msg-icon {
  background: #e4f7ee;
  color: #2d8d77;
}
.msg-content {
  border-radius: 14px;
  background: #f6f7fb;
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.85;
  word-break: break-word;
}
.msg-content :deep(.katex-display) {
  margin: 0.6em 0;
  overflow-x: auto;
}
.panel-md {
  font-size: 12px;
  line-height: 1.8;
  color: #3f4660;
  margin-top: 8px;
}
.panel-md :deep(.katex-display) {
  margin: 0.5em 0;
  overflow-x: auto;
}
.message.mine .msg-content {
  background: #ebe8ff;
}
.msg-meta {
  font-size: 10px;
  color: #a5aab9;
  margin-top: 6px;
}
.composer {
  padding: 19px 22px;
  border-top: 1px solid var(--border);
}
.composer-box {
  border: 1px solid #dee0ec;
  border-radius: 14px;
  padding: 12px;
}
.composer textarea {
  width: 100%;
  border: 0;
  outline: 0;
  resize: vertical;
  min-height: 54px;
}
.composer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.qa-aside {
  padding: 20px;
  height: max-content;
}
.suggestion {
  display: block;
  width: 100%;
  border: 1px solid #eaeaf2;
  border-radius: 12px;
  padding: 13px;
  background: #fff;
  text-align: left;
  color: #59617d;
  font-size: 12px;
  line-height: 1.8;
  margin: 9px 0;
}
.mini-callout {
  background: #f1f0ff;
  border-radius: 13px;
  padding: 17px;
  font-size: 12px;
  color: #645a9a;
  line-height: 1.8;
}
.line {
  height: 1px;
  background: var(--border);
  margin: 18px 0;
}
.review-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 20px;
  margin-top: 23px;
}
.review-main {
  padding: 26px;
}
.review-detail {
  padding: 24px;
  height: max-content;
}
.tabs {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 13px;
  margin-bottom: 20px;
}
.tab {
  padding: 10px 15px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: #8a90a6;
  font-weight: 750;
}
.tab.active {
  background: var(--primary-soft);
  color: var(--primary);
}
.wrong-item {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}
.wrong-item h4 {
  margin: 0 0 8px;
  font-size: 14px;
}
.wrong-item p {
  font-size: 12px;
  color: #6e758f;
  margin: 4px 0;
}
.notice {
  font-size: 11px;
  line-height: 1.8;
  color: #9381a1;
  border-radius: 12px;
  background: #faf7ff;
  border: 1px solid #f1ebff;
  padding: 12px 14px;
}
.compact {
  font-size: 12px;
  color: #6c738c;
  line-height: 1.8;
}
.empty {
  padding: 40px 20px;
  text-align: center;
  color: #9aa0b3;
}
.footer-note {
  margin-top: 34px;
  color: #a2a5b8;
  font-size: 11px;
  text-align: center;
}
.tiny {
  font-size: 11px;
  color: var(--muted);
}
.err {
  color: var(--bad);
}
.mobile-only {
  display: none !important;
}
@media (max-width: 950px) {
  .workspace-main,
  .qa-grid,
  .review-grid,
  .catalog-layout,
  .stats-row,
  .three-cols {
    grid-template-columns: 1fr;
  }
  .topic-grid {
    grid-template-columns: 1fr;
  }
  .avatar-panel {
    position: static;
  }
}

/* —— 手机端（对齐原型：顶栏 + 底栏 + 单列可读） —— */
@media (max-width: 720px) {
  .desktop-only {
    display: none !important;
  }
  .mobile-only {
    display: flex !important;
  }
  .shell {
    display: flex;
    flex-direction: column;
    min-height: 100dvh;
    background: #f7f8fd;
  }
  .m-app-header {
    position: sticky;
    top: 0;
    z-index: 20;
    height: 58px;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 8px 14px;
    background: rgba(255, 255, 255, 0.94);
    border-bottom: 1px solid #ececf6;
    backdrop-filter: blur(12px);
  }
  .m-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }
  .m-brand .brand-mark {
    width: 36px;
    height: 36px;
    font-size: 16px;
    flex: none;
  }
  .m-brand-text {
    min-width: 0;
  }
  .m-brand-text strong {
    display: block;
    font-size: 15px;
    color: #20223e;
  }
  .m-brand-text small {
    display: block;
    margin-top: 2px;
    font-size: 11px;
    color: #9299ad;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 58vw;
  }
  .m-user-chip {
    width: 34px;
    height: 34px;
    border: 0;
    border-radius: 11px;
    background: #efeaff;
    color: #544ba7;
    font-weight: 800;
    flex: none;
  }
  .m-status-bar {
    display: flex !important;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 14px 0;
    font-size: 11px;
    color: #8a91ab;
  }
  .main {
    flex: 1;
    min-width: 0;
  }
  .content {
    padding: 14px 14px calc(88px + env(safe-area-inset-bottom));
    max-width: none;
  }
  .content.home-mode {
    height: calc(100dvh - 58px - 28px - 64px - env(safe-area-inset-bottom));
    max-height: calc(100dvh - 58px - 28px - 64px - env(safe-area-inset-bottom));
    padding: 12px 14px 10px;
  }
  .m-bottom-nav {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 30;
    height: calc(64px + env(safe-area-inset-bottom));
    display: grid !important;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom));
    background: #fff;
    border-top: 1px solid #ebeaf5;
    box-shadow: 0 -8px 24px rgba(40, 41, 90, 0.06);
  }
  .m-bottom-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    border: 0;
    background: transparent;
    color: #989cb0;
    font-size: 11px;
    font-weight: 700;
    border-radius: 12px;
    min-width: 0;
    padding: 6px 0;
  }
  .m-bottom-item .m-ico {
    font-size: 14px;
    line-height: 1;
  }
  .m-bottom-item.active {
    color: #6c59e9;
    background: #f4f1ff;
  }
  .h1 {
    font-size: 22px;
    line-height: 1.35;
  }
  .h2 {
    font-size: 18px;
  }
  .sub {
    font-size: 13px;
    line-height: 1.7;
  }
  .hero {
    display: flex;
    flex-direction: column-reverse;
    min-height: 0;
    border-radius: 20px;
  }
  .hero-copy {
    padding: 18px 16px 20px;
  }
  .hero-brand {
    margin-bottom: 14px;
  }
  .hero-mark {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  .hero-brand strong {
    font-size: 17px;
  }
  .hero h1 {
    font-size: 24px;
    max-width: none;
  }
  .hero-art {
    width: 100%;
    min-height: 220px;
    max-width: none;
    padding: 14px;
  }
  .hero-art :deep(.avatar-scene) {
    height: 160px;
  }
  .hero-buttons {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    margin-top: 14px;
  }
  .hero-buttons .btn {
    width: 100%;
  }
  .section-row {
    margin: 20px 0 12px;
    align-items: flex-start;
  }
  .section-label {
    display: none;
  }
  .stats-row,
  .three-cols,
  .topic-grid,
  .workspace-main,
  .review-grid,
  .catalog-layout {
    grid-template-columns: 1fr !important;
    gap: 12px;
  }
  .stat,
  .feature-card,
  .topic-card,
  .card {
    min-height: 0;
  }
  .feature-card {
    padding: 16px;
  }
  .catalog-head {
    display: block;
  }
  .catalog-topics-head {
    align-items: stretch;
  }
  .catalog-topics-head .search {
    width: 100%;
    min-width: 0;
  }
  .search {
    margin-top: 12px;
    width: 100%;
    min-width: 0;
  }
  .chapter-panel {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 8px;
    -webkit-overflow-scrolling: touch;
  }
  .chapter-title {
    display: none;
  }
  .chapter-btn {
    white-space: nowrap;
    width: auto;
    flex: 0 0 auto;
  }
  .topic-card {
    padding: 16px;
  }
  .topic-card h3 {
    font-size: 16px;
  }
  .topic-card p {
    font-size: 12px;
  }
  .workspace-header {
    display: block;
    margin-bottom: 12px;
  }
  .workspace-header > .btn {
    margin-top: 10px;
  }
  .workspace-main {
    display: flex !important;
    flex-direction: column;
    gap: 12px;
  }
  .workspace-main .avatar-panel {
    order: -1;
    padding: 12px;
  }
  .lesson-card {
    padding: 16px 14px;
    min-height: 0;
  }
  .lesson-body h2 {
    font-size: 20px;
  }
  .lesson-body p,
  .lesson-md,
  .intro-plain {
    font-size: 14px;
    line-height: 1.85;
  }
  .step-list.two-steps {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .step {
    font-size: 12px;
    justify-content: center;
  }
  .exit-teach,
  .coach-actions,
  .composer-footer,
  .note-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .exit-teach .btn,
  .coach-actions .btn,
  .composer-footer .btn,
  .note-actions .btn {
    width: 100%;
  }
  .coach-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .ask-inline,
  .ask-log,
  .chatlog {
    max-height: none;
  }
  .chatlog.ask-log {
    max-height: 42vh;
  }
  .message {
    max-width: 100%;
  }
  .tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  .tab {
    flex: 0 0 auto;
    white-space: nowrap;
  }
  .quiz,
  .option,
  .formula,
  .concept-box,
  .note-item {
    word-break: break-word;
  }
  .md-table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .composer-box textarea {
    font-size: 14px;
  }
  .footer-note {
    font-size: 10px;
    margin-top: 18px;
    padding-bottom: 8px;
  }
}
</style>
