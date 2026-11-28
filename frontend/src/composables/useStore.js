import { reactive, watch } from "vue";

const BASE_KEY = "zhixu_ai_v2_store";
let activeUserId = "";
let hydrating = false;

function storageKey(uid = activeUserId) {
  return uid ? `${BASE_KEY}:${uid}` : `${BASE_KEY}:guest`;
}

function loadFor(uid) {
  if (!uid) return { progress: {}, wrong: [], lastTopicId: "lecture_ch2" };
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey(uid)) || "{}");
    return {
      progress: parsed.progress && typeof parsed.progress === "object" ? parsed.progress : {},
      wrong: Array.isArray(parsed.wrong) ? parsed.wrong : [],
      lastTopicId: parsed.lastTopicId || "lecture_ch2",
    };
  } catch {
    return { progress: {}, wrong: [], lastTopicId: "lecture_ch2" };
  }
}

export const store = reactive({
  progress: {},
  wrong: [],
  lastTopicId: "lecture_ch2",
});

function persistCurrent() {
  if (hydrating || !activeUserId) return;
  try {
    localStorage.setItem(
      storageKey(activeUserId),
      JSON.stringify({
        progress: store.progress,
        wrong: store.wrong,
        lastTopicId: store.lastTopicId,
      })
    );
  } catch {
    /* ignore quota */
  }
}

watch(store, persistCurrent, { deep: true, flush: "sync" });

/** 按当前登录用户隔离本地学习进度与错题记录；登出时清空内存状态 */
export function switchStoreUser(userId) {
  const nextId = userId ? String(userId) : "";
  activeUserId = nextId;
  hydrating = true;
  try {
    const data = loadFor(nextId);
    store.progress = data.progress;
    store.wrong = data.wrong;
    store.lastTopicId = data.lastTopicId || "lecture_ch2";
  } finally {
    hydrating = false;
  }
}

export function saveProgress(topicId, patch) {
  store.lastTopicId = topicId;
  store.progress[topicId] = {
    ...(store.progress[topicId] || {}),
    ...patch,
    updated: Date.now(),
  };
}

/** 按唯一题目 ID 统计已答题目数，防止「重做本题」重复刷高完成度 */
export function recordQuizAnswer(topicId, questionId, quizTotal, extra = {}) {
  const prev = store.progress[topicId] || {};
  const prevIds = Array.isArray(prev.answeredIds) ? prev.answeredIds : [];
  const nextIds = questionId && !prevIds.includes(questionId) ? [...prevIds, questionId] : prevIds;
  const count = questionId ? nextIds.length : Math.max(Number(prev.answered) || 0, nextIds.length);
  saveProgress(topicId, {
    ...extra,
    answeredIds: nextIds,
    answered: count,
    quizTotal: quizTotal || Number(prev.quizTotal) || 8,
  });
}

/** 同一知识点同一道错题合并更新最新一次作答，避免重复刷出多条相同错题 */
export function addWrong(item) {
  const idx = store.wrong.findIndex(
    (x) =>
      x.topic === item.topic &&
      (item.questionId && x.questionId ? x.questionId === item.questionId : x.question === item.question)
  );
  const entry = { ...item, date: Date.now() };
  if (idx >= 0) {
    store.wrong.splice(idx, 1);
  }
  store.wrong.push(entry);
}

export function wrongFor(topicId) {
  return store.wrong.filter((x) => x.topic === topicId);
}

export function numLearned() {
  return Object.keys(store.progress).length;
}

/** 只清当前账号学习记录，保留登录态 */
export function clearLearningData() {
  store.progress = {};
  store.wrong = [];
  store.lastTopicId = "lecture_ch2";
  if (activeUserId) {
    try {
      localStorage.removeItem(storageKey(activeUserId));
    } catch {
      /* ignore */
    }
  }
}
