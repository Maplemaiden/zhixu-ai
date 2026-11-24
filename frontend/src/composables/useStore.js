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
