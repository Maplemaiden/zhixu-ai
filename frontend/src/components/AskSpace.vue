<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { api } from "../api";
import { chapters, readyTopics } from "../data/catalog";
import { useSpeech } from "../composables/useSpeech";
import { renderRichText } from "../utils/renderRichText";

const props = defineProps({
  backendOk: { type: Boolean, default: true },
  seedQuestion: { type: String, default: "" },
});

const emit = defineEmits(["back", "open-topic", "seed-consumed"]);

const { speaking, paused, currentLine, stop, speakText, pause, resume } = useSpeech();

const input = ref("");
const loading = ref(false);
const error = ref("");
const messages = ref([]);
const logEl = ref(null);
const inputEl = ref(null);
let askAbort = null;
let askReqId = 0;

function formatSourceItem(s) {
  const cleanTitle = String(s?.title || "").replace(/^#+\s*/, "").trim();
  return `${s?.source || ""}${cleanTitle ? " · " + cleanTitle : ""}`;
}

const catalogGroups = computed(() =>
  chapters
    .map((ch) => ({
      id: ch.id,
      title: ch.title,
      topics: (ch.topics || []).filter((t) => t.status === "ready"),
    }))
    .filter((g) => g.topics.length)
);
const readyCount = computed(() => readyTopics().length);

const suggestionPages = [
  [
    "风险型和不确定型怎么区分？",
    "期望值准则和决策树有什么关系？",
    "AHP 和 TOPSIS 分别适合什么情况？",
    "用一个小例子讲讲后悔值准则",
  ],
  [
    "效用是在衡量什么？",
    "DEA 适合比较什么样的单位？",
    "目标规划里的偏差变量是什么？",
    "马尔可夫链的无后效性怎么理解？",
  ],
  [
    "贝叶斯决策为什么要修正概率？",
    "乐观准则和悲观准则差在哪？",
    "多属性决策的权重从哪来？",
    "离散事件仿真在解决什么问题？",
  ],
];
const pageIndex = ref(0);
const rollPaused = ref(false);
const visibleSuggestions = computed(() => suggestionPages[pageIndex.value]);
let rollTimer = null;

function nextSuggestionPage() {
  pageIndex.value = (pageIndex.value + 1) % suggestionPages.length;
}

async function scrollBottom() {
  await nextTick();
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight;
}

function useSuggestion(q) {
  input.value = q;
  nextTick(() => {
    const el = inputEl.value;
    if (!el) return;
    el.focus();
    const len = el.value.length;
    el.setSelectionRange(len, len);
  });
}

function clearChat() {
  askReqId += 1;
  if (askAbort) {
    try {
      askAbort.abort();
    } catch {
      /* ignore */
    }
    askAbort = null;
  }
  loading.value = false;
  messages.value = [];
  error.value = "";
  stop();
}

async function send() {
  const q = input.value.trim();
  if (!q || loading.value || !props.backendOk) return;
  const myId = ++askReqId;
  const ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
  askAbort = ctrl;
  const history = messages.value
    .filter((m) => (m.role === "user" || m.role === "assistant") && m.topic !== "系统")
    .slice(-6)
    .map((m) => ({ role: m.role, text: m.text }));
  loading.value = true;
  error.value = "";
  messages.value.push({ role: "user", text: q });
  input.value = "";
  await scrollBottom();
  try {
    const res = await api.ask(q, "course", {
      section: null,
      sectionLabel: "全课答疑",
      history,
      signal: ctrl?.signal,
    });
    if (myId !== askReqId) return;
    const answer = res.answer || "暂时没有生成回答，请换个问法再试。";
    messages.value.push({
      role: "assistant",
      text: answer,
      sources: res.sources || [],
      topic: "知知",
    });
    speakText(String(answer).replace(/[#*`$]/g, " ").replace(/\s+/g, " ").slice(0, 360));
  } catch (e) {
    if (myId !== askReqId || e?.name === "AbortError") return;
    error.value = e.message || String(e);
    messages.value.push({
      role: "assistant",
      text: `抱歉，这次没有答上：${error.value}`,
      topic: "系统",
    });
  } finally {
    if (myId === askReqId) {
      loading.value = false;
      askAbort = null;
      await scrollBottom();
    }
  }
}

function onKeydown(e) {
  if (e.isComposing || e.keyCode === 229) return;
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

function speakLast() {
  const last = [...messages.value].reverse().find((m) => m.role === "assistant");
  if (last) speakText(String(last.text).replace(/\s+/g, " ").slice(0, 360));
}

function openRelated(topicId) {
  stop();
  emit("open-topic", topicId);
}

watch(
  () => props.seedQuestion,
  async (q) => {
    const text = String(q || "").trim();
    if (!text) return;
    input.value = text;
    emit("seed-consumed");
    await nextTick();
    await send();
  },
  { immediate: true }
);

onMounted(() => {
  rollTimer = setInterval(() => {
    if (!rollPaused.value && !messages.value.length) nextSuggestionPage();
  }, 10000);
});
onUnmounted(() => {
  if (rollTimer) clearInterval(rollTimer);
  if (askAbort) {
    try {
      askAbort.abort();
    } catch {
      /* ignore */
    }
  }
  stop();
});

defineExpose({ clearChat });
</script>

<template>
  <section class="ask-space" aria-label="答疑空间">
    <div class="ask-layout">
      <div class="ask-chat">
        <header class="ask-chat-head">
          <div>
            <h1>答疑空间</h1>
            <p>《决策理论与方法》全课答疑 · 可从右侧进知识点</p>
          </div>
          <div class="ask-chat-links">
            <button class="linkish" type="button" :disabled="!messages.length && !loading" @click="clearChat">清空</button>
            <button class="linkish" type="button" @click="emit('back')">回首页</button>
          </div>
        </header>

        <div ref="logEl" class="chat-stage">
          <div v-if="!messages.length" class="welcome">
            <p class="welcome-lead">直接问知知。概念、方法分流、解题步骤都可以。</p>
            <div
              class="suggest-viewport"
              @mouseenter="rollPaused = true"
              @mouseleave="rollPaused = false"
            >
              <Transition name="suggest-roll" mode="out-in">
                <div class="suggest-row" :key="pageIndex">
                  <button
                    v-for="s in visibleSuggestions"
                    :key="s"
                    class="chip"
                    type="button"
                    @click="useSuggestion(s)"
                  >
                    {{ s }}
                  </button>
                </div>
              </Transition>
            </div>
          </div>

          <div v-for="(m, i) in messages" :key="i" class="bubble-row" :class="{ mine: m.role === 'user' }">
            <div class="bubble-icon">{{ m.role === "user" ? "我" : "知" }}</div>
            <div class="bubble">
              <div
                class="bubble-text"
                v-html="renderRichText(m.text, { math: m.role !== 'user' })"
              />
              <div class="bubble-meta">{{ m.role === "user" ? "学生" : m.topic || "知知" }}</div>
              <div v-if="m.sources?.length" class="bubble-sources">
                教材来源：
                <span v-for="(s, si) in m.sources" :key="si">
                  {{ formatSourceItem(s) }}{{ si < m.sources.length - 1 ? "；" : "" }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="loading" class="thinking">知知思考中…</div>
        </div>

        <footer class="composer">
          <div v-if="messages.length" class="suggest-row compact">
            <button
              v-for="s in visibleSuggestions.slice(0, 3)"
              :key="s"
              class="chip"
              type="button"
              @click="useSuggestion(s)"
            >
              {{ s }}
            </button>
          </div>
          <div class="composer-box">
            <textarea
              ref="inputEl"
              v-model="input"
              rows="2"
              placeholder="输入问题，Enter 发送…"
              @keydown="onKeydown"
            />
            <button
              class="send-btn"
              type="button"
              :disabled="loading || !backendOk || !input.trim()"
              @click="send"
            >
              {{ loading ? "…" : "发送" }}
            </button>
          </div>
          <div class="composer-foot">
            <button class="linkish" type="button" :disabled="!messages.length" @click="speakLast">口播上一条</button>
            <span class="composer-hint">Shift+Enter 换行</span>
          </div>
          <p v-if="error" class="err">{{ error }}</p>
        </footer>
      </div>

      <aside class="ask-aside">
        <div class="ask-aside-head">
          <h2>课程目录</h2>
          <p>答完可点进对应知识点系统学</p>
        </div>
        <div class="ask-aside-scroll">
          <section v-for="g in catalogGroups" :key="g.id" class="ask-catalog-group">
            <h3>{{ g.title }}</h3>
            <button
              v-for="t in g.topics"
              :key="t.id"
              class="ask-topic-link"
              type="button"
              @click="openRelated(t.id)"
            >
              <span>{{ t.title }}</span>
              <small>{{ t.type }}</small>
            </button>
          </section>
        </div>
        <div class="ask-aside-foot">
          <p class="ask-aside-tip">共 {{ readyCount }} 个可学知识点</p>
          <div class="ask-aside-status" :class="{ live: speaking && !paused }">
            <span class="dot" />
            {{ speaking ? (paused ? "口播已暂停" : "知知口播中") : "待命" }}
            <button v-if="speaking" class="linkish" type="button" @click="paused ? resume() : pause()">
              {{ paused ? "继续" : "暂停" }}
            </button>
            <button v-if="speaking || currentLine" class="linkish" type="button" @click="stop">停止</button>
          </div>
        </div>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.ask-space {
  height: 100%;
  min-height: 0;
  color: var(--ink);
  display: flex;
  flex-direction: column;
}
.ask-layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(260px, 0.72fr);
  gap: 16px;
}
.ask-chat {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 22px;
  border: 1px solid var(--border);
  background: #fff;
  box-shadow: var(--shadow);
  overflow: hidden;
}
.ask-chat-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px 12px;
  border-bottom: 1px solid #eceef5;
  flex-shrink: 0;
  background: #fbfbff;
}
.ask-chat-head h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: var(--ink);
}
.ask-chat-head p {
  margin: 5px 0 0;
  font-size: 12px;
  color: var(--muted);
  font-weight: 650;
}
.ask-chat-links {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  padding-top: 4px;
}
.chat-stage {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 18px;
  scrollbar-width: thin;
  background: #fff;
}
.welcome {
  margin: 6vh auto 0;
  max-width: 560px;
  text-align: center;
}
.welcome-lead {
  margin: 0 0 18px;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text);
}
.suggest-viewport {
  overflow: hidden;
  min-height: 108px;
}
.suggest-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}
.suggest-roll-enter-active,
.suggest-roll-leave-active {
  transition: transform 0.45s ease, opacity 0.45s ease;
}
.suggest-roll-enter-from {
  transform: translateY(22px);
  opacity: 0;
}
.suggest-roll-leave-to {
  transform: translateY(-22px);
  opacity: 0;
}
.suggest-row.compact {
  justify-content: flex-start;
  margin-bottom: 12px;
}
.chip {
  border: 1px solid #e6e7f2;
  background: #fff;
  color: #5b6280;
  border-radius: 999px;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}
.chip:hover {
  border-color: #cfc8f5;
  background: #f6f4ff;
  color: #4f46a8;
}
.bubble-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: flex-start;
}
.bubble-row.mine {
  flex-direction: row-reverse;
}
.bubble-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary-soft);
  color: var(--primary);
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  flex: none;
}
.bubble-row.mine .bubble-icon {
  background: #ebe8ff;
  color: #4f46a8;
}
.bubble {
  max-width: min(92%, 680px);
  background: #f7f8fc;
  border: 1px solid #eceef5;
  border-radius: 18px;
  padding: 14px 16px;
  color: var(--text);
}
.bubble-row.mine .bubble {
  background: #ebe8ff;
  border-color: transparent;
  color: var(--ink);
}
.bubble-text {
  font-size: 15px;
  line-height: 1.75;
  overflow-wrap: anywhere;
}
.bubble-text :deep(.md-p) {
  margin: 0 0 0.55em;
}
.bubble-text :deep(.md-p:last-child),
.bubble-text :deep(.md-h:last-child) {
  margin-bottom: 0;
}
.bubble-text :deep(.md-h) {
  margin: 0.35em 0 0.55em;
}
.bubble-text :deep(.md-ul),
.bubble-text :deep(.md-ol) {
  margin: 0.35em 0 0.65em;
  padding-left: 1.35em;
}
.bubble-text :deep(li) {
  margin: 0.2em 0;
}
.bubble-text :deep(strong) {
  font-weight: 800;
  color: var(--ink);
}
.bubble-text :deep(code) {
  font-size: 0.92em;
  padding: 0.05em 0.35em;
  border-radius: 5px;
  background: rgba(102, 88, 223, 0.08);
}
.bubble-meta {
  margin-top: 8px;
  font-size: 11px;
  color: #a5aab9;
}
.bubble-row.mine .bubble-meta {
  color: #8a84b8;
}
.bubble-sources {
  margin-top: 8px;
  font-size: 12px;
  color: #6b5fad;
  line-height: 1.5;
}
.thinking {
  margin: 8px 0 0 48px;
  font-size: 13px;
  color: var(--primary);
  font-weight: 650;
}
.composer {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  border-top: 1px solid #eceef5;
  background: #fbfbff;
}
.composer-box {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: end;
  padding: 12px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e2e4ef;
}
.composer-box:focus-within {
  border-color: #c8c3f2;
  box-shadow: 0 0 0 3px rgba(102, 88, 223, 0.08);
}
.composer textarea {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 8px 6px;
  resize: none;
  min-height: 52px;
  max-height: 140px;
  font: inherit;
  font-size: 15px;
  line-height: 1.55;
  color: var(--ink);
}
.composer textarea:focus {
  outline: none;
}
.composer textarea::placeholder {
  color: #9aa1b5;
}
.send-btn {
  border: 0;
  border-radius: 14px;
  min-width: 72px;
  height: 44px;
  padding: 0 16px;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
}
.send-btn:hover:not(:disabled) {
  background: #5749c9;
}
.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.composer-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}
.linkish {
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 650;
  padding: 0;
  cursor: pointer;
}
.linkish:hover:not(:disabled) {
  color: var(--primary);
}
.linkish:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.composer-hint {
  font-size: 11px;
  color: #a5aab9;
}
.err {
  margin: 8px 0 0;
  color: var(--bad);
  font-size: 13px;
}
.ask-aside {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: 22px;
  border: 1px solid var(--border);
  background: #fff;
  box-shadow: var(--shadow);
  overflow: hidden;
}
.ask-aside-head {
  padding: 16px 16px 12px;
  border-bottom: 1px solid #eceef5;
  background: #fbfbff;
  flex-shrink: 0;
}
.ask-aside-head h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 850;
  color: var(--ink);
}
.ask-aside-head p {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}
.ask-aside-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 12px 14px;
  scrollbar-width: thin;
}
.ask-catalog-group {
  margin-bottom: 14px;
}
.ask-catalog-group h3 {
  margin: 0 0 8px;
  padding: 0 4px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #8a90a5;
}
.ask-topic-link {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  text-align: left;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 12px;
  padding: 9px 10px;
  cursor: pointer;
  color: var(--ink);
}
.ask-topic-link:hover {
  background: #f6f4ff;
  border-color: #e4dff8;
}
.ask-topic-link span {
  font-size: 13px;
  font-weight: 700;
  line-height: 1.4;
}
.ask-topic-link small {
  font-size: 11px;
  color: var(--muted);
}
.ask-aside-foot {
  flex-shrink: 0;
  padding: 12px 14px 14px;
  border-top: 1px solid #eceef5;
  background: #fbfbff;
}
.ask-aside-tip {
  margin: 0 0 8px;
  font-size: 11px;
  color: #a5aab9;
}
.ask-aside-status {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  font-weight: 650;
  color: var(--muted);
}
.ask-aside-status .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c5cada;
}
.ask-aside-status.live .dot {
  background: #52b996;
  box-shadow: 0 0 0 3px rgba(82, 185, 150, 0.2);
}
.ask-aside-status.live {
  color: #158a65;
}
@media (max-width: 980px) {
  .ask-layout {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(0, 1fr) minmax(180px, 32vh);
  }
  .ask-aside {
    order: 1;
  }
  .welcome {
    margin-top: 3vh;
  }
}
@media (max-width: 720px) {
  .composer-hint {
    display: none;
  }
  .ask-chat-head h1 {
    font-size: 18px;
  }
}
</style>
