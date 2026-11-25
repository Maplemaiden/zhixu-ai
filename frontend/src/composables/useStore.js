import { reactive, watch } from "vue";

const KEY = "zhixu_ai_v1_store";

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "{}");
  } catch {
    return {};
  }
}

const raw = load();
export const store = reactive({
  progress: raw.progress || {},
  wrong: raw.wrong || [],
  lastTopicId: raw.lastTopicId || "expected_value",
});

watch(
  store,
  () => {
    try {
      localStorage.setItem(
        KEY,
        JSON.stringify({
          progress: store.progress,
          wrong: store.wrong,
          lastTopicId: store.lastTopicId,
        })
      );
    } catch {
      /* ignore quota */
    }
  },
  { deep: true }
);

export function saveProgress(topicId, patch) {
  store.lastTopicId = topicId;
  store.progress[topicId] = {
    ...(store.progress[topicId] || {}),
    ...patch,
    updated: Date.now(),
  };
}

export function addWrong(item) {
  store.wrong.push({ ...item, date: Date.now() });
}

export function wrongFor(topicId) {
  return store.wrong.filter((x) => x.topic === topicId);
}

export function numLearned() {
  return Object.keys(store.progress).length;
}

/** 只清学习记录，保留登录态（localStorage.clear() 会连 token 一起清掉导致被登出） */
export function clearLearningData() {
  store.progress = {};
  store.wrong = [];
  store.lastTopicId = "expected_value";
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
